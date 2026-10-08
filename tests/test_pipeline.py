import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('pipeline', Path(__file__).parents[1] / 'lambda' / 'app.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class FakeS3:
    def __init__(self, objects):
        self.objects = objects
        self.writes = []
        self.bodies = []

    def get_object(self, Bucket, Key):
        body = io.BytesIO(self.objects[Key])
        self.bodies.append(body)
        return {'Body': body}

    def put_object(self, **kwargs):
        self.writes.append(kwargs)


def event(*keys):
    return {'Records': [{'eventSource': 'aws:s3', 'eventName': 'ObjectCreated:Put', 's3': {'bucket': {'name': 'synthetic-bucket'}, 'object': {'key': key}}} for key in keys]}


class PipelineTests(unittest.TestCase):
    def test_multiple_urlencoded_events_and_precise_prefix(self):
        client = FakeS3({'raw/sales report.csv': b'item,total\nDemo,10\n', 'raw/nested/raw/report.csv': b'item,total\nOther,20\n'})
        with patch.object(app.boto3, 'client', return_value=client):
            result = app.handler(event('raw/sales+report.csv', 'raw/nested/raw/report.csv'), None)
        self.assertEqual(result['count'], 2)
        self.assertEqual([w['Key'] for w in client.writes], ['curated/sales report.csv', 'curated/nested/raw/report.csv'])
        self.assertTrue(all(b.closed for b in client.bodies))
        self.assertEqual(client.writes[0]['ContentType'], 'text/csv; charset=utf-8')

    def test_curated_and_non_csv_inputs_are_skipped(self):
        client = FakeS3({})
        with patch.object(app.boto3, 'client', return_value=client):
            result = app.handler(event('curated/report.csv', 'raw/image.png'), None)
        self.assertEqual(result['skipped'], 2)
        self.assertEqual(client.writes, [])

    def test_cp1252_punctuation_and_utf8_bom(self):
        output, count = app.normalize_csv('name\n“Demo”\n'.encode('cp1252'))
        self.assertEqual(output.decode('utf-8'), 'name\n“Demo”\n')
        self.assertEqual(count, 1)
        output, _ = app.normalize_csv(b'\xef\xbb\xbfitem\r\nDemo\r\n')
        self.assertEqual(output, b'item\nDemo\n')

    def test_header_only_csv_replaces_output_with_empty_dataset(self):
        client = FakeS3({'raw/report.csv': b'item,total\n'})
        with patch.object(app.boto3, 'client', return_value=client):
            result = app.handler(event('raw/report.csv'), None)
        self.assertEqual(result['count'], 0)
        self.assertEqual(client.writes[0]['Body'], b'item,total\n')

    def test_malformed_rows_and_headers_are_rejected(self):
        for data in (b'', b'a,a\n1,2\n', b'a,b\n1\n', b'a,b\n1,2,3\n', b',b\n1,2\n'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                app.normalize_csv(data)

    def test_oversized_object_is_rejected_before_download(self):
        client = FakeS3({})
        payload = event('raw/report.csv')
        payload['Records'][0]['s3']['object']['size'] = app.MAX_BYTES + 1
        with patch.object(app.boto3, 'client', return_value=client), self.assertRaises(ValueError):
            app.handler(payload, None)
        self.assertEqual(client.bodies, [])

    def test_read_size_limit_and_body_cleanup_on_error(self):
        client = FakeS3({'raw/report.csv': b'a\n' + b'x' * app.MAX_BYTES})
        with patch.object(app.boto3, 'client', return_value=client), self.assertRaises(ValueError):
            app.handler(event('raw/report.csv'), None)
        self.assertTrue(client.bodies[0].closed)
        self.assertEqual(client.writes, [])


if __name__ == '__main__':
    unittest.main()

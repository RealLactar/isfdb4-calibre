"""Offline open/read failure diagnostics and exception-preservation contracts."""
import io
import socket
import ssl
import traceback
from urllib.error import HTTPError, URLError
from unittest.mock import Mock, patch

from calibre_plugins.isfdb4 import objects


class HttpDiagnostics:
    diagnostic_url = 'https://www.isfdb.org/cgi-bin/title.cgi?101'
    diagnostic_final_url = 'https://www.isfdb.org/cgi-bin/title.cgi?102'

    def assert_transport_failure(self, error, stage='open', logger=None):
        logger = logger if logger is not None else self.log
        response = self.response(b'', self.diagnostic_final_url)
        origin_traceback = []
        original_cause = error.__cause__

        def transport_origin(*args, **kwargs):
            try:
                raise error
            except Exception:
                origin_traceback.append(error.__traceback__)
                raise

        if stage == 'open':
            fetch = Mock(side_effect=transport_origin)
        elif stage == 'geturl':
            response.geturl.side_effect = transport_origin
            fetch = Mock(return_value=response)
        else:
            response.read.side_effect = transport_origin
            fetch = Mock(return_value=response)
        with patch.object(objects, 'urlopen', fetch):
            try:
                objects.fetch_isfdb_url(self.diagnostic_url, 30, logger, self.prefs)
            except Exception as caught:
                self.assertIs(caught, error)
                self.assertIs(caught.__cause__, original_cause)
                chain = []
                current = caught.__traceback__
                while current is not None:
                    chain.append(current)
                    current = current.tb_next
                self.assertTrue(any(tb is origin_traceback[0] for tb in chain))
                self.assertEqual(chain[-1].tb_frame.f_code.co_name, 'transport_origin')
                frames = traceback.extract_tb(caught.__traceback__)
                self.assertEqual(sum(frame.name == 'fetch_isfdb_url' for frame in frames), 1)
            else:
                self.fail('Transport failure was hidden behind a successful result')
        fetch.assert_called_once()
        self.assertEqual(fetch.call_args.kwargs['timeout'], 90)
        return response

    def test_http_diagnostics_statuses_preserve_exception_and_traceback(self):
        for stage in ('open', 'read'):
            for code in (403, 404, 429, 500):
                with self.subTest(stage=stage, code=code):
                    self.log.reset_mock()
                    error = HTTPError(self.diagnostic_url, code, 'synthetic response', {}, None)
                    self.assert_transport_failure(error, stage)
                    self.log.error.assert_called_once()
                    message = self.log.error.call_args.args[0]
                    self.assertIn('HTTP ' + str(code), message)
                    self.assertIn(self.diagnostic_url, message)
                    self.assertIn('reading response body' if stage == 'read' else 'opening response', message)
                    self.assertNotIn('Cloudflare', message)
                    self.assertNotIn('bot', message)

    def test_http_diagnostics_direct_socket_and_request_timeouts(self):
        for error in (socket.timeout('socket timed out'), TimeoutError('request deadline exceeded')):
            with self.subTest(error=repr(error)):
                self.log.reset_mock()
                self.assert_transport_failure(error)
                self.assertIn('TimeoutError', self.log.error.call_args.args[0])

    def test_http_diagnostics_wrapped_timeouts(self):
        caused = RuntimeError('request failed')
        caused.__cause__ = TimeoutError('request deadline exceeded')
        errors = [URLError(socket.timeout('socket timed out')),
                  URLError(URLError(TimeoutError('nested timeout'))),
                  OSError(TimeoutError('wrapped socket timeout')), caused]
        for error in errors:
            with self.subTest(error=repr(error)):
                self.log.reset_mock()
                self.assert_transport_failure(error)
                self.assertIn('TimeoutError', self.log.error.call_args.args[0])
                self.assertIn('transport reason=', self.log.error.call_args.args[0])

    def test_http_diagnostics_refused_and_reset_connections(self):
        errors = [ConnectionRefusedError('connection refused'), ConnectionResetError('connection reset'),
                  URLError(ConnectionRefusedError('connection refused')),
                  URLError(ConnectionResetError('connection reset'))]
        for error in errors:
            with self.subTest(error=repr(error)):
                self.log.reset_mock()
                self.assert_transport_failure(error)
                self.assertIn(repr(error), self.log.error.call_args.args[0])

    def test_http_diagnostics_read_failure_reports_redirect_and_preserves_error(self):
        for error in (OSError('stream read failed'), socket.timeout('read timed out'),
                      URLError(TimeoutError('wrapped read timeout'))):
            with self.subTest(error=repr(error)):
                self.log.reset_mock()
                response = self.assert_transport_failure(error, 'read')
                response.read.assert_called_once()
                message = self.log.error.call_args.args[0]
                self.assertIn('reading response body', message)
                self.assertIn(self.diagnostic_final_url, message)

    def test_http_diagnostics_geturl_failure_is_not_masked(self):
        self.assert_transport_failure(ValueError('response URL unavailable'), 'geturl')
        self.assertIn('reading response URL', self.log.error.call_args.args[0])

    def test_http_diagnostics_logging_failure_cannot_mask_transport_error(self):
        logger = Mock(error=Mock(side_effect=RuntimeError('logging failed')))
        self.assert_transport_failure(ConnectionResetError('original reset'), logger=logger)
        logger.error.assert_called_once()

    def test_http_diagnostics_exception_without_getcode(self):
        error = ValueError('transport wrapper without HTTP methods')
        self.assert_transport_failure(error)
        self.assertIn('ValueError', self.log.error.call_args.args[0])

    def test_http_diagnostics_empty_body_preserves_existing_empty_root_policy(self):
        for body in (b'', b' \t\r\n'):
            with self.subTest(body=body):
                self.log.reset_mock()
                with patch.object(objects, 'urlopen', return_value=self.response(body, self.diagnostic_final_url)) as fetch:
                    location, root = objects.fetch_isfdb_url(self.diagnostic_url, 30, self.log, self.prefs)
                self.assertEqual(location, self.diagnostic_final_url)
                self.assertEqual(root.text_content(), '')
                fetch.assert_called_once()
                self.log.error.assert_called_once()
                message = self.log.error.call_args.args[0]
                self.assertIn('Empty ISFDB response', message)
                self.assertIn(self.diagnostic_url, message)
                self.assertIn(self.diagnostic_final_url, message)
                self.assertNotIn('%s', message)

    def test_http_diagnostics_success_keeps_decode_headers_tls_and_timeout(self):
        for requested_timeout in (30, 120):
            with self.subTest(timeout=requested_timeout):
                self.log.reset_mock()
                with patch.object(objects, 'urlopen', return_value=self.response(b'<html><body><p>Caf\xe9 &amp; th\xe9</p></body></html>', self.diagnostic_final_url)) as fetch:
                    location, root = objects.fetch_isfdb_url(self.diagnostic_url, requested_timeout, self.log, self.prefs)
                self.assertEqual(location, self.diagnostic_final_url)
                self.assertEqual(root.xpath('//p/text()'), ['Caf\u00e9 & th\u00e9'])
                self.assertEqual(fetch.call_args.kwargs['timeout'], max(requested_timeout, 90))
                self.assertEqual(fetch.call_args.kwargs['context'].verify_mode, ssl.CERT_NONE)
                self.assertFalse(fetch.call_args.kwargs['context'].check_hostname)
                request = fetch.call_args.args[0]
                self.assertEqual(request.get_method(), 'GET')
                self.assertEqual(dict((k.lower(), v) for k, v in request.header_items()),
                                 dict((k.lower(), v) for k, v in objects.ISFDB_HTTP_HEADERS.items()))
                self.log.error.assert_not_called()

    def test_http_diagnostics_render_with_real_calibre_logger(self):
        from calibre.ebooks.metadata.sources.base import create_log
        output = io.StringIO()
        logger = create_log(output)
        self.assert_transport_failure(HTTPError(self.diagnostic_url, 403, 'synthetic denial', {}, None), logger=logger)
        message = output.getvalue()
        self.assertIn('HTTP 403', message)
        self.assertIn(self.diagnostic_url, message)
        self.assertIn('timeout=90s', message)

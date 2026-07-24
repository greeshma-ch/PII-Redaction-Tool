from detectors.ip_address import IPAddressDetector
from detectors.base import IP_ADDRESS

def test_valid_ips():
    detector = IPAddressDetector()
    text = "IPv4: 192.168.1.1 and IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334 or ::1."
    results = detector.detect(text)
    assert len(results) == 3
    assert results[0].text == "192.168.1.1"
    assert results[0].confidence == 0.95
    assert results[1].text == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    assert results[1].confidence == 0.9

def test_invalid_ips():
    detector = IPAddressDetector()
    text = "Invalid octets 256.1.1.1. Version number 1.0.0."
    results = detector.detect(text)
    assert len(results) == 0

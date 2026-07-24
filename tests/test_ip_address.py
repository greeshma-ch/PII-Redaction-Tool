from detectors.ip_address import IPAddressDetector
from detectors.base import IP_ADDRESS


def test_valid_ipv4():
    detector = IPAddressDetector()
    text = "Server at 192.168.1.1 is running."
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text == "192.168.1.1"
    assert results[0].pii_type == IP_ADDRESS
    assert results[0].confidence == 0.95


def test_valid_ipv6():
    detector = IPAddressDetector()
    text = "IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334."
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].confidence == 0.9


def test_invalid_octets():
    detector = IPAddressDetector()
    text = "Invalid octets 256.1.1.1."
    results = detector.detect(text)
    assert len(results) == 0


def test_version_number_not_matched():
    detector = IPAddressDetector()
    text = "Version number 1.0.0."
    results = detector.detect(text)
    assert len(results) == 0

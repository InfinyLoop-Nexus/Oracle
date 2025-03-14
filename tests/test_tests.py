import pytest #redundant import test

def test_always_fails():
    assert False, "This test is designed to always fail"

def test_always_passes():
    assert True, "This test is designed to always pass"

#formating test
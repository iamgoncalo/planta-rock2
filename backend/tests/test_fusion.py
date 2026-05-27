"""
Tests for the sensor fusion service.
"""
from __future__ import annotations

import pytest

from app.services.fusion import fuse, redistribute_weights


class TestFusion:
    def test_all_three_sources_weighted_average(self):
        """Fusion with all 3 sources should give correct weighted result."""
        ir = 80.0
        wifi = 60.0
        camera = 40.0
        # With camera_ml_confidence=1.0:
        # effective weights: IR=0.5, WiFi=0.3, Camera=0.2
        # expected = 80*0.5 + 60*0.3 + 40*0.2 = 40 + 18 + 8 = 66.0
        occ, conf, sources = fuse(ir_occupancy=ir, wifi_occupancy=wifi, camera_occupancy=camera)
        assert abs(occ - 66.0) < 0.01
        assert set(sources) == {"IR", "WiFi", "Camera"}

    def test_all_sources_confidence_is_100(self):
        """With all 3 sources at full ML confidence, confidence should be 100%."""
        _, conf, _ = fuse(ir_occupancy=50.0, wifi_occupancy=50.0, camera_occupancy=50.0)
        assert conf == 100.0

    def test_missing_camera_redistributes_weights(self):
        """Without camera, IR and WiFi weights should be redistributed to sum 1."""
        ir = 80.0
        wifi = 60.0
        # Without camera: raw weights IR=0.5, WiFi=0.3 → sum=0.8
        # normalised: IR=0.625, WiFi=0.375
        # expected = 80*0.625 + 60*0.375 = 50 + 22.5 = 72.5
        occ, conf, sources = fuse(ir_occupancy=ir, wifi_occupancy=wifi, camera_occupancy=None)
        assert abs(occ - 72.5) < 0.01
        assert "Camera" not in sources
        assert set(sources) == {"IR", "WiFi"}

    def test_missing_camera_lowers_confidence(self):
        """Confidence should drop when fewer sources are available."""
        _, conf_all, _ = fuse(50.0, 50.0, 50.0)
        _, conf_no_cam, _ = fuse(50.0, 50.0, None)
        assert conf_no_cam < conf_all

    def test_only_ir_returns_ir_value(self):
        """With only IR available, fused occupancy should equal IR value."""
        ir = 75.0
        occ, conf, sources = fuse(ir_occupancy=ir, wifi_occupancy=None, camera_occupancy=None)
        assert abs(occ - ir) < 0.01
        assert sources == ["IR"]

    def test_only_ir_confidence_reduced(self):
        """Only 1 of 3 sources — confidence should be significantly lower than 100."""
        _, conf, _ = fuse(ir_occupancy=50.0, wifi_occupancy=None, camera_occupancy=None)
        assert conf < 100.0
        assert conf >= 0.0

    def test_no_sources_returns_zero(self):
        """With no sources, occupancy and confidence should be 0."""
        occ, conf, sources = fuse()
        assert occ == 0.0
        assert conf == 0.0
        assert sources == []

    def test_only_wifi(self):
        """Only WiFi source available."""
        occ, conf, sources = fuse(wifi_occupancy=45.0)
        assert abs(occ - 45.0) < 0.01
        assert sources == ["WiFi"]
        assert conf < 100.0

    def test_only_camera_with_low_confidence(self):
        """Camera with low ML confidence should reduce fusion confidence."""
        _, conf_high, _ = fuse(camera_occupancy=50.0, camera_ml_confidence=1.0)
        _, conf_low, _ = fuse(camera_occupancy=50.0, camera_ml_confidence=0.1)
        assert conf_low < conf_high

    def test_camera_with_zero_confidence_excluded(self):
        """Camera with 0 ML confidence contributes 0 weight."""
        # camera weight = 0.2 * 0.0 = 0.0, only IR and WiFi contribute
        occ, _, sources = fuse(
            ir_occupancy=80.0,
            wifi_occupancy=60.0,
            camera_occupancy=20.0,
            camera_ml_confidence=0.0,
        )
        # With camera weight=0, IR=0.5, WiFi=0.3 → norm IR=0.625, WiFi=0.375
        expected = 80.0 * 0.625 + 60.0 * 0.375
        assert abs(occ - expected) < 0.5  # slight tolerance for normalisation

    def test_occupancy_always_in_range(self):
        """Fused occupancy must always be in [0, 100]."""
        occ, _, _ = fuse(ir_occupancy=200.0, wifi_occupancy=150.0, camera_occupancy=120.0)
        assert 0.0 <= occ <= 100.0

    def test_redistribute_weights_two_sources(self):
        """redistribute_weights with IR+WiFi should return normalised weights."""
        weights = redistribute_weights(["IR", "WiFi"])
        assert abs(sum(weights.values()) - 1.0) < 0.001
        assert weights["IR"] > weights["WiFi"]  # IR has higher base weight

    def test_redistribute_weights_single_source(self):
        weights = redistribute_weights(["IR"])
        assert abs(weights["IR"] - 1.0) < 0.001

    def test_redistribute_weights_empty(self):
        weights = redistribute_weights([])
        assert weights == {}

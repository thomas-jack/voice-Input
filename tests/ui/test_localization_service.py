"""UILocalizationService Tests

Tests for UI localization service that handles language switching and translation.
This is a v0.5.3 feature that provides app-wide i18n support.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtCore import QCoreApplication

from sonicinput.core.services.ui_services import UILocalizationService
from sonicinput.core.services.config.config_keys import ConfigKeys


class TestUILocalizationServiceBasics:
    """Test basic UILocalizationService functionality"""

    def test_service_creation(self, mock_config_service):
        """Test localization service can be created"""
        mock_event_service = MagicMock()
        service = UILocalizationService(mock_config_service, mock_event_service)
        assert service is not None
        assert service.config_service == mock_config_service
        assert service.event_service == mock_event_service

    def test_get_supported_languages(self, mock_config_service):
        """Test getting supported languages returns correct dict"""
        mock_event_service = MagicMock()
        service = UILocalizationService(mock_config_service, mock_event_service)
        languages = service.get_supported_languages()

        assert isinstance(languages, dict)
        assert "auto" in languages
        assert "en-US" in languages
        assert "zh-CN" in languages
        assert languages["auto"] == "System (Auto)"
        assert languages["en-US"] == "English"
        assert languages["zh-CN"] == "Simplified Chinese"


class TestLanguageResolution:
    """Test language code resolution and normalization"""

    def test_normalize_language_code_basic(self, mock_config_service):
        """Test basic language code normalization"""
        mock_event_service = MagicMock()
        service = UILocalizationService(mock_config_service, mock_event_service)

        assert service._normalize_language_code("en-US") == "en-US"
        assert service._normalize_language_code("zh-CN") == "zh-CN"
        assert service._normalize_language_code("auto") == "auto"

    def test_normalize_language_code_case_insensitive(self, mock_config_service):
        """Test language code normalization is case insensitive"""
        mock_event_service = MagicMock()
        service = UILocalizationService(mock_config_service, mock_event_service)

        assert service._normalize_language_code("EN-us") == "en-US"
        assert service._normalize_language_code("ZH-cn") == "zh-CN"
        assert service._normalize_language_code("AUTO") == "auto"

    def test_normalize_language_code_underscore_to_dash(self, mock_config_service):
        """Test language code normalization converts underscore to dash"""
        mock_event_service = MagicMock()
        service = UILocalizationService(mock_config_service, mock_event_service)

        assert service._normalize_language_code("en_US") == "en-US"
        assert service._normalize_language_code("zh_CN") == "zh-CN"

    def test_normalize_language_code_short_form(self, mock_config_service):
        """Test short language codes are expanded"""
        mock_event_service = MagicMock()
        service = UILocalizationService(mock_config_service, mock_event_service)

        assert service._normalize_language_code("en") == "en-US"
        assert service._normalize_language_code("zh") == "zh-CN"

    def test_resolve_language_auto(self, mock_config_service):
        """Test resolving 'auto' uses system locale"""
        mock_event_service = MagicMock()
        service = UILocalizationService(mock_config_service, mock_event_service)

        with patch.object(service, '_get_system_locale', return_value='zh-CN'):
            resolved = service._resolve_language("auto")
            assert resolved == "zh-CN"

    def test_resolve_language_fallback_to_english(self, mock_config_service):
        """Test unsupported languages fall back to English"""
        mock_event_service = MagicMock()
        service = UILocalizationService(mock_config_service, mock_event_service)

        resolved = service._resolve_language("fr-FR")  # French not supported
        assert resolved == "en-US"


class TestLanguageConfiguration:
    """Test language configuration retrieval"""

    def test_get_configured_language_default(self, mock_config_service):
        """Test getting configured language returns 'auto' by default"""
        mock_event_service = MagicMock()
        mock_config_service.get_setting = Mock(return_value=None)

        service = UILocalizationService(mock_config_service, mock_event_service)
        language = service.get_configured_language()

        assert language == "auto"
        mock_config_service.get_setting.assert_called_once_with(ConfigKeys.UI_LANGUAGE, "auto")

    def test_get_configured_language_explicit(self, mock_config_service):
        """Test getting explicitly configured language"""
        mock_event_service = MagicMock()
        mock_config_service.get_setting = Mock(return_value="zh-CN")

        service = UILocalizationService(mock_config_service, mock_event_service)
        language = service.get_configured_language()

        assert language == "zh-CN"

    def test_get_active_language_before_apply(self, mock_config_service):
        """Test getting active language before apply_language is called"""
        mock_event_service = MagicMock()
        mock_config_service.get_setting = Mock(return_value="zh-CN")

        service = UILocalizationService(mock_config_service, mock_event_service)

        with patch.object(service, '_get_system_locale', return_value='zh-CN'):
            active = service.get_active_language()
            assert active == "zh-CN"


class TestLanguageApplication:
    """Test applying language changes to the UI"""

    def test_apply_language_default(self, mock_config_service, qtbot):
        """Test applying default language (English)"""
        mock_event_service = MagicMock()
        mock_config_service.get_setting = Mock(return_value="en-US")

        service = UILocalizationService(mock_config_service, mock_event_service)

        # Apply English (should succeed without translation file)
        result = service.apply_language("en-US")
        assert result == "en-US"
        assert service._current_language == "en-US"

    def test_apply_language_emits_event(self, mock_config_service, qtbot):
        """Test applying language emits UI_LANGUAGE_CHANGED event"""
        mock_event_service = MagicMock()
        mock_config_service.get_setting = Mock(return_value="en-US")

        service = UILocalizationService(mock_config_service, mock_event_service)
        service.apply_language("en-US")

        # Verify event was emitted
        mock_event_service.emit.assert_called_once()
        call_args = mock_event_service.emit.call_args
        # Event name is lowercase
        assert "ui_language_changed" in str(call_args).lower()

        # Check event data
        event_data = call_args[0][1]
        assert event_data["language"] == "en-US"
        assert "applied" in event_data

    def test_apply_language_idempotent(self, mock_config_service, qtbot):
        """Test applying same language twice doesn't reinstall translator"""
        mock_event_service = MagicMock()
        mock_config_service.get_setting = Mock(return_value="en-US")

        service = UILocalizationService(mock_config_service, mock_event_service)

        # First apply
        service.apply_language("en-US")
        first_call_count = mock_event_service.emit.call_count

        # Second apply (should be idempotent)
        service.apply_language("en-US")

        # Should not emit event again if language unchanged
        assert mock_event_service.emit.call_count == first_call_count

    def test_apply_language_with_none_uses_configured(self, mock_config_service, qtbot):
        """Test applying language with None uses configured language"""
        mock_event_service = MagicMock()
        mock_config_service.get_setting = Mock(return_value="zh-CN")

        service = UILocalizationService(mock_config_service, mock_event_service)

        with patch.object(service, '_get_system_locale', return_value='zh-CN'):
            result = service.apply_language(None)
            assert result == "zh-CN"


class TestTranslationFileHandling:
    """Test translation file loading and handling"""

    def test_translation_dir_resolution(self, mock_config_service):
        """Test translation directory is correctly resolved"""
        mock_event_service = MagicMock()
        service = UILocalizationService(mock_config_service, mock_event_service)

        assert service._translation_dir is not None
        assert isinstance(service._translation_dir, Path)
        # Should end with 'assets/i18n'
        assert service._translation_dir.parts[-2:] == ('assets', 'i18n')

    def test_install_translator_english_no_file_needed(self, mock_config_service, qtbot):
        """Test English doesn't require translation file"""
        # Create QApplication if not exists
        app = QCoreApplication.instance()
        if app is None:
            app = QCoreApplication([])

        mock_event_service = MagicMock()
        service = UILocalizationService(mock_config_service, mock_event_service)

        result = service._install_translator("en-US")
        assert result is True  # English always succeeds

    def test_install_translator_missing_file(self, mock_config_service, qtbot):
        """Test installing translator with missing translation file"""
        # Create QApplication if not exists
        app = QCoreApplication.instance()
        if app is None:
            app = QCoreApplication([])

        mock_event_service = MagicMock()
        service = UILocalizationService(mock_config_service, mock_event_service)

        # Try to install a non-existent translation
        with patch.object(Path, 'exists', return_value=False):
            result = service._install_translator("fr-FR")
            assert result is False


class TestSystemLocaleDetection:
    """Test system locale detection"""

    def test_get_system_locale_success(self, mock_config_service):
        """Test getting system locale succeeds"""
        mock_event_service = MagicMock()
        service = UILocalizationService(mock_config_service, mock_event_service)

        locale = service._get_system_locale()
        assert isinstance(locale, str)
        assert len(locale) > 0

    def test_get_system_locale_fallback(self, mock_config_service):
        """Test getting system locale falls back to en-US on error"""
        mock_event_service = MagicMock()
        service = UILocalizationService(mock_config_service, mock_event_service)

        # Mock QLocale.system() to raise exception
        with patch('PySide6.QtCore.QLocale.system', side_effect=Exception("Test error")):
            locale = service._get_system_locale()
            assert locale == "en-US"


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""

    def test_user_changes_language_in_settings(self, mock_config_service, qtbot):
        """Test complete workflow: user changes language in settings"""
        mock_event_service = MagicMock()

        # Start with English
        mock_config_service.get_setting = Mock(return_value="en-US")
        service = UILocalizationService(mock_config_service, mock_event_service)
        service.apply_language("en-US")

        # User changes to Chinese
        mock_config_service.get_setting = Mock(return_value="zh-CN")
        result = service.apply_language("zh-CN")

        assert result == "zh-CN"
        assert service._current_language == "zh-CN"
        assert mock_event_service.emit.call_count >= 1

    def test_auto_language_follows_system(self, mock_config_service, qtbot):
        """Test 'auto' language correctly follows system locale"""
        mock_event_service = MagicMock()
        mock_config_service.get_setting = Mock(return_value="auto")

        service = UILocalizationService(mock_config_service, mock_event_service)

        # Mock Chinese system locale
        with patch.object(service, '_get_system_locale', return_value='zh-CN'):
            result = service.apply_language("auto")
            assert result == "zh-CN"

        # Mock English system locale
        with patch.object(service, '_get_system_locale', return_value='en-US'):
            result = service.apply_language("auto")
            assert result == "en-US"


# Fixtures for this test module
@pytest.fixture
def mock_config_service():
    """Mock config service for localization tests"""
    mock = MagicMock()
    mock.get_setting = Mock(return_value="auto")
    return mock

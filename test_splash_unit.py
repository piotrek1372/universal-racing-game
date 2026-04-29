#!/usr/bin/env python3
"""
Unit test for SplashManager functionality.
Tests the SplashManager class without requiring a full Panda3D runtime.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Mock Panda3D before importing
sys.modules['panda3d'] = MagicMock()
sys.modules['panda3d.core'] = MagicMock()
sys.modules['panda3d.core'].TransparencyAttrib = MagicMock()
sys.modules['panda3d.core'].CardMaker = MagicMock()
sys.modules['direct'] = MagicMock()
sys.modules['direct.gui'] = MagicMock()
sys.modules['direct.gui.DirectGui'] = MagicMock()
sys.modules['direct.interval'] = MagicMock()
sys.modules['direct.interval.IntervalGlobal'] = MagicMock()

# Now import the SplashManager
from src.ui_manager import SplashManager

def test_splash_manager_initialization():
    """Test that SplashManager initializes correctly."""
    print("Test 1: SplashManager initialization")
    
    mock_base = Mock()
    mock_base.render2d = Mock()
    
    # Create a mock for loader
    mock_base.loader = Mock()
    mock_base.loader.loadTexture = Mock(return_value=Mock())
    
    # Create a mock for CardMaker
    mock_card = Mock()
    mock_card.generate = Mock(return_value=Mock())
    
    with patch('src.ui_manager.CardMaker', return_value=mock_card):
        with patch('src.ui_manager.loader', mock_base.loader):
            splash = SplashManager(mock_base, on_complete=lambda: None)
            
            assert splash.base == mock_base
            assert splash.on_complete is not None
            assert splash.is_active == False
            print("  [OK] SplashManager initialized correctly")

def test_splash_manager_paths():
    """Test that paths are set up correctly."""
    print("\nTest 2: Path setup")
    
    mock_base = Mock()
    mock_base.render2d = Mock()
    mock_base.loader = Mock()
    mock_base.loader.loadTexture = Mock(return_value=Mock())
    
    mock_card = Mock()
    mock_card.generate = Mock(return_value=Mock())
    
    with patch('src.ui_manager.CardMaker', return_value=mock_card):
        with patch('src.ui_manager.loader', mock_base.loader):
            splash = SplashManager(mock_base)
            
            # Check that paths were set up
            assert hasattr(splash, 'splash_images')
            assert hasattr(splash, 'audio_file')
            print("  [OK] Paths configured")
            
            # Check that splash images were found
            if splash.splash_images:
                print(f"  [OK] Found {len(splash.splash_images)} splash images")
            else:
                print("  [WARNING] No splash images found")

def test_splash_manager_sequence_creation():
    """Test that sequence can be created."""
    print("\nTest 3: Sequence creation")
    
    mock_base = Mock()
    mock_base.render2d = Mock()
    mock_base.loader = Mock()
    mock_base.loader.loadTexture = Mock(return_value=Mock())
    
    mock_card = Mock()
    mock_card.generate = Mock(return_value=Mock())
    
    with patch('src.ui_manager.CardMaker', return_value=mock_card):
        with patch('src.ui_manager.loader', mock_base.loader):
            with patch('src.ui_manager.Sequence') as mock_sequence:
                mock_sequence.return_value = Mock()
                
                splash = SplashManager(mock_base)
                seq = splash._create_sequence()
                
                assert seq is not None
                print("  [OK] Sequence created successfully")

if __name__ == "__main__":
    print("=" * 60)
    print("SplashManager Unit Tests")
    print("=" * 60)
    
    try:
        test_splash_manager_initialization()
        test_splash_manager_paths()
        test_splash_manager_sequence_creation()
        
        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
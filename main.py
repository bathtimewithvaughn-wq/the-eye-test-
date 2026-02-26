#!/usr/bin/env python3
"""
The Eye Test - Football Video Processor
Main entry point
"""

import sys

try:
    from PyQt5.QtWidgets import QApplication
    from gui.main_window import MainWindow
except Exception as e:
    print(f"[FATAL] Import error: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to close...")
    sys.exit(1)


def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("The Eye Test")
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec_())
    except Exception as e:
        print(f"[FATAL] Runtime error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to close...")
        sys.exit(1)


if __name__ == '__main__':
    main()

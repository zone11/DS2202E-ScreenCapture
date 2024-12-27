# DS2202E-ScreenCapture
```DS2202E-ScreenCapture.py``` is a Python script that captures whatever is displayed on the screen of a Rigol DS2202E series oscilloscope.

It can save data as a WYSIWYG (What You See Is What You Get) picture of the oscilloscope screen, or as a text file in CSV (Comma Separated Values) format.

To achieve this, SCPI (Standard Commands for Programmable Instruments) are sent from the computer to the oscilloscope, using the LXI (LAN-based eXtensions for Instrumentation) protocol over a Telnet connection.
The computer and the oscilloscope are connected together by a LAN (Local Area Network).
No USB (Universal Serial Bus), no VISA (Virtual Instrument Software Architecture), no IVI (Interchangeable Virtual Instrument) and no Rigol drivers are required.


Based on work of RoGeorge - https://github.com/RoGeorge/DS1054Z_screen_capture
Additional work by doug-a-brunner for Python3 support - https://github.com/doug-a-brunner

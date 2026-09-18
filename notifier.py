import sys
import os
import time
import threading
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

class Notifier:
    def __init__(self, sound_duration=30):
        self.sound_duration = sound_duration
        self._stop_alert = threading.Event()
        self._alert_thread = None

    def _play_siren(self):
        """Alternating high-pitch siren to grab immediate attention."""
        start = time.time()
        while not self._stop_alert.is_set() and (time.time() - start < self.sound_duration):
            if HAS_WINSOUND:
                try:
                    winsound.Beep(1200, 250)
                    winsound.Beep(1800, 250)
                except Exception:
                    sys.stdout.write("\a")
                    sys.stdout.flush()
                    time.sleep(0.5)
            else:
                sys.stdout.write("\a")
                sys.stdout.flush()
                time.sleep(0.5)

    def trigger_sound_alert(self):
        """Starts alarm in a background thread."""
        self._stop_alert.clear()
        self._alert_thread = threading.Thread(target=self._play_siren, daemon=True)
        self._alert_thread.start()

    def stop_sound_alert(self):
        self._stop_alert.set()

    def send_desktop_notification(self, title: str, message: str):
        """Sends native Windows toast notification."""
        clean_title = title.replace('"', '`"').replace("'", "''")
        clean_msg = message.replace('"', '`"').replace("'", "''")

        ps_script = f"""
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $xml = [xml]$template.GetXml()
        $textNodes = $xml.GetElementsByTagName('text')
        $textNodes[0].AppendChild($xml.CreateTextNode('{clean_title}')) | Out-Null
        $textNodes[1].AppendChild($xml.CreateTextNode('{clean_msg}')) | Out-Null
        $toastXml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $toastXml.LoadXml($xml.OuterXml)
        $toast = [Windows.UI.Notifications.ToastNotification]::new($toastXml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Amazon Stock Bot').Show($toast)
        """
        try:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"[Notifier] Desktop toast error: {e}")

    def notify_in_stock(self, product_name: str, price: str, url: str):
        print("\n" + "="*60)
        print("[!] [!] [!] ITEM IN STOCK! [!] [!] [!]")
        print(f"Product: {product_name}")
        print(f"Price:   {price}")
        print(f"URL:     {url}")
        print("="*60 + "\n")

        self.trigger_sound_alert()
        self.send_desktop_notification(
            title="[IN STOCK] Amazon Canada Alert",
            message=f"{product_name} is in stock for {price}! Check your browser!"
        )

if __name__ == "__main__":
    notifier = Notifier(sound_duration=3)
    print("Testing desktop notification and 3s sound alert...")
    notifier.notify_in_stock(
        product_name="Nintendo Switch 2 - Zelda 40th Anniversary",
        price="$649.99 CAD",
        url="https://www.amazon.ca/..."
    )
    time.sleep(3)
    print("Test complete.")

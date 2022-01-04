import argparse
from datetime import datetime as dt
from pathlib import Path
import subprocess


def main(w, h, r, q, a):
    image = Path(f"/home/pi/{dt.now().strftime('%Y-%m-%dT%H%M%S')}.jpg")
    subprocess.run(["raspistill", "-o", image, "--width", w, "--height", h, "--rotation", r, "--quality", q, "--awb", a])
    subprocess.run(["scp", str(image.absolute()), "pi@192.168.1.104:/home/pi/images/raw"])
    image.unlink()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", default="800")
    parser.add_argument("--height", default="600")
    parser.add_argument("--rotation", default="0")
    parser.add_argument("--quality", default="50")
    parser.add_argument("--awb", default="auto")
    args = parser.parse_args()
    main(args.width, args.height, args.rotation, args.quality, args.awb)

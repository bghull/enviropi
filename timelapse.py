import argparse
import subprocess
from datetime import date
from pathlib import Path

IMAGE_DIR = Path("/home/pi/images")


def _filedate(file):
    return date.fromisoformat(file.name[:10])


def find_images_between(start, end, glob):
    imgs = sorted([img.name for img in glob if _filedate(img) >= start and _filedate(img) <= end])
    if not imgs:
        raise FileNotFoundError("No images matching that date")
    return imgs


def main(start, end, duration):
    imgs = find_images_between(start, end, IMAGE_DIR.glob("*.jpg"))
    secs_per_frame = round(duration / len(imgs), 2)
    txt = IMAGE_DIR / "images.txt"
    with txt.open("w") as f:
        for i in imgs:
            f.write(f"file '{i}'\nduration {secs_per_frame}\n")
    if start == end:
        outfile = f"{start.strftime('%Y-%m-%d')}.mp4"
    else:
        outfile = f"{start.strftime('%Y-%m-%d')}_to_{end.strftime('%Y-%m-%d')}.mp4"
    target = IMAGE_DIR / "gifs" / outfile
    ffmpeg_cmd = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        f"{txt}",
        "-pix_fmt",
        "yuv420p",
        f"{target}",
        "-y",
    ]
    print(
        f"creating gif: {len(imgs)} images @ {duration}s total runtime ({secs_per_frame} sec/frame)..."
    )
    print(ffmpeg_cmd)
    subprocess.run(ffmpeg_cmd)
    print("done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--today",
        action="store_true",
        help="Finds images from today's date only.\
            Cannot be used with --start or --end",
    )
    parser.add_argument("--start", help="Date string in YYYY-MM-DD format")
    parser.add_argument(
        "--end",
        help="Date string in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Total runtime of the final mp4.\
            Used to calculate the time each image should be displayed (i.e. seconds-per-frame).\
                Default is %(default)s",
    )
    args = parser.parse_args()
    if args.today and (args.start or args.end):
        raise TypeError("Specify EITHER --today OR --start and --end dates, but not both")
    elif args.today:
        start = date.today()
        end = start
    elif args.start and args.end:
        try:
            start = date.fromisoformat(args.start)
            end = date.fromisoformat(args.end)
        except ValueError:
            raise ValueError("--start and --end must be in YYYY-MM-DD format")
        except Exception as err:
            raise err
    else:
        raise TypeError(
            "Missing args: specify either --today OR --start and --end dates in YYYY-MM-DD format"
        )
    main(start, end, args.duration)

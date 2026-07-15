"""Простая автоматизация: убрать фон с фото и вписать в квадрат 512x512.

Использование:
    python extras/bg_remove_resize.py
    python extras/bg_remove_resize.py --input input --output output --size 512 --force

Берёт все файлы .png/.jpg/.jpeg/.webp из папки `input/`, удаляет фон
(библиотека `rembg`) и вписывает объект в прозрачный квадрат заданного
размера (по умолчанию 512x512 — размер Telegram custom emoji, letterbox
с сохранением пропорций, без обрезки), сохраняет результат в `output/`
под тем же именем файла (расширение всегда .png, т.к. нужен альфа-канал).

Обработанные файлы не пересобираются повторно при повторном запуске
(если исходник не менялся) — используй --force, чтобы пересобрать всё.
"""

from __future__ import annotations

import argparse
import logging
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image
from rembg import remove

# Allow running as `python extras/bg_remove_resize.py` from repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from bot.constants import (  # noqa: E402
    DEFAULT_EMOJI_IMAGE_SIZE,
    DEFAULT_INPUT_DIR,
    DEFAULT_OUTPUT_DIR,
    EXTRAS_LOG_FORMAT,
    SUPPORTED_IMAGE_EXTENSIONS,
)

logger = logging.getLogger(__name__)

try:
    _RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:  # старые версии Pillow (<9.1)
    _RESAMPLE = Image.LANCZOS


def remove_background(input_path: Path) -> Image.Image:
    """Загружает изображение и удаляет фон, возвращает RGBA-картинку."""
    with Image.open(input_path) as src:
        result = remove(src.convert("RGBA"))

    if not isinstance(result, Image.Image):
        result = Image.open(BytesIO(result))

    return result.convert("RGBA")


def frame_square(image: Image.Image, size: int) -> Image.Image:
    """Вписывает изображение в прозрачный квадрат size x size без обрезки."""
    rgba = image.convert("RGBA")
    width, height = rgba.size

    if width == 0 or height == 0:
        scaled = rgba
    else:
        scale = min(size / width, size / height)
        new_width = max(1, round(width * scale))
        new_height = max(1, round(height * scale))
        scaled = rgba.resize((new_width, new_height), _RESAMPLE)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    x = (size - scaled.width) // 2
    y = (size - scaled.height) // 2
    canvas.paste(scaled, (x, y), scaled)
    return canvas


def process_image(input_path: Path, output_dir: Path, size: int, force: bool) -> Path:
    """Обрабатывает один файл и сохраняет PNG в output_dir под тем же именем."""
    output_path = output_dir / f"{input_path.stem}.png"

    if (
        not force
        and output_path.exists()
        and output_path.stat().st_mtime >= input_path.stat().st_mtime
    ):
        logger.info("Пропуск (уже обработан): %s", output_path)
        return output_path

    logger.info("Обработка: %s", input_path)
    no_bg = remove_background(input_path)
    framed = frame_square(no_bg, size=size)
    framed.save(output_path, format="PNG")
    logger.info("Сохранено: %s", output_path)
    return output_path


def process_batch(
    input_dir: Path, output_dir: Path, size: int, force: bool
) -> tuple[list[Path], list[Path]]:
    """Обрабатывает все поддерживаемые файлы из input_dir. Возвращает (успешные, файлы с ошибкой)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    succeeded: list[Path] = []
    failed: list[Path] = []

    files = sorted(
        p
        for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    )

    if not files:
        logger.warning(
            "В %s нет изображений (поддерживаются: %s)",
            input_dir,
            ", ".join(SUPPORTED_IMAGE_EXTENSIONS),
        )
        return succeeded, failed

    for path in files:
        try:
            succeeded.append(process_image(path, output_dir, size, force))
        except Exception:
            logger.exception("Ошибка обработки файла %s", path)
            failed.append(path)

    return succeeded, failed


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            f"Удаление фона + приведение к квадрату "
            f"(по умолчанию {DEFAULT_EMOJI_IMAGE_SIZE}x{DEFAULT_EMOJI_IMAGE_SIZE})"
        )
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_DIR,
        help=f"Папка с исходными фото (по умолчанию {DEFAULT_INPUT_DIR}/)",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Папка для результата (по умолчанию {DEFAULT_OUTPUT_DIR}/)",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_EMOJI_IMAGE_SIZE,
        help=f"Сторона квадрата в пикселях (по умолчанию {DEFAULT_EMOJI_IMAGE_SIZE})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Пересобрать все файлы, даже если уже готовы",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Подробный лог (DEBUG)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format=EXTRAS_LOG_FORMAT,
    )

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not input_dir.is_dir():
        logger.error("Папка не найдена: %s", input_dir)
        raise SystemExit(1)

    succeeded, failed = process_batch(input_dir, output_dir, args.size, args.force)
    logger.info("Готово: успешно %d, с ошибками %d.", len(succeeded), len(failed))
    if failed:
        logger.info("Файлы с ошибками: %s", ", ".join(p.name for p in failed))


if __name__ == "__main__":
    main()

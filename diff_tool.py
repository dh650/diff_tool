import os
import sys
import argparse
import difflib
import signal
import threading

similar_pairs = []
total_comparisons = 0
lock = threading.Lock()

def safe_print(*args, **kwargs):
    with lock:
        kwargs.setdefault('end', '\n')
        kwargs['flush'] = True
        print(*args, **kwargs)

def signal_handler(sig, frame, output_file=None):
    safe_print("\n\n[Прерывание по Ctrl+C]")
    safe_print(f"Сравнено пар: {total_comparisons}")
    safe_print(f"Найдено похожих пар (≥50%): {len(similar_pairs)}")

    if similar_pairs:
        safe_print("\nНайденные похожие файлы (до прерывания):")
        safe_print("-" * 120)
        safe_print(f"{'Файл 1':<40} | {'Файл 2':<40} | {'Сходство':<10}")
        safe_print("-" * 120)
        for (file1, file2), similarity in similar_pairs:
            safe_print(f"{os.path.basename(file1):<40} | {os.path.basename(file2):<40} | {similarity:7.1f}%")
            safe_print(f"  {file1}")
            safe_print(f"  {file2}")
            safe_print("-" * 120)

        if output_file:
            print_results_to_file(similar_pairs, total_comparisons, output_file)
    else:
        safe_print("\nПохожих пар не найдено")

    sys.exit(0)

def print_results(similar_pairs, total_comparisons, output_file=None):
    if output_file:
        print_results_to_file(similar_pairs, total_comparisons, output_file)
    else:
        print(f"\nСравнено пар: {total_comparisons}")
        print(f"Найдено похожих пар (≥50%): {len(similar_pairs)}")

        if similar_pairs:
            print("\nПохожие файлы:")
            print("-" * 120)
            print(f"{'Файл 1':<40} | {'Файл 2':<40} | {'Сходство':<10}")
            print("-" * 120)

            for (file1, file2), similarity in similar_pairs:
                print(f"{os.path.basename(file1):<40} | {os.path.basename(file2):<40} | {similarity:7.1f}%")
                print(f"  {file1}")
                print(f"  {file2}")
                print("-" * 120)
        else:
            print("\nПохожих пар не найдено")

def print_results_to_file(similar_pairs, total_comparisons, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Сравнено пар: {total_comparisons}\n")
            f.write(f"Найдено похожих пар (≥50%): {len(similar_pairs)}\n\n")

            if similar_pairs:
                f.write("Похожие файлы:\n")
                f.write("-" * 120 + "\n")
                f.write(f"{'Файл 1':<40} | {'Файл 2':<40} | {'Сходство':<10}\n")
                f.write("-" * 120 + "\n")

                for (file1, file2), similarity in similar_pairs:
                    f.write(f"{os.path.basename(file1):<40} | {os.path.basename(file2):<40} | {similarity:7.1f}%\n")
                    f.write(f"  {file1}\n")
                    f.write(f"  {file2}\n")
                    f.write("-" * 120 + "\n")
            else:
                f.write("Похожих пар не найдено\n")

        safe_print(f"\nРезультаты сохранены в файл: {output_file}")
    except Exception as e:
        safe_print(f"Ошибка записи в файл {output_file}: {e}")

def find_files(folder_path, extension, exclude_extensions=None, all_files=False):
    if exclude_extensions is None:
        exclude_extensions = []

    files = []
    for root, dirs, files_list in os.walk(folder_path):
        for file in files_list:
            if all_files:
                if not any(file.endswith(ext) for ext in exclude_extensions):
                    full_path = os.path.join(root, file)
                    files.append(full_path)
            else:
                if file.endswith(extension) and not any(file.endswith(ext) for ext in exclude_extensions):
                    full_path = os.path.join(root, file)
                    files.append(full_path)
    return files

def find_loc_files(folder_path, extension, exclude_extensions=None, all_files=False):
    if exclude_extensions is None:
        exclude_extensions = []

    loc_files = []
    for root, dirs, files_list in os.walk(folder_path):
        current_folder = os.path.basename(root)
        if 'LOC' in current_folder.upper():
            for file in files_list:
                if all_files:
                    if not any(file.endswith(ext) for ext in exclude_extensions):
                        full_path = os.path.join(root, file)
                        loc_files.append(full_path)
                else:
                    if file.endswith(extension) and not any(file.endswith(ext) for ext in exclude_extensions):
                        full_path = os.path.join(root, file)
                        loc_files.append(full_path)
    return loc_files

def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.readlines()
    except Exception:
        return []

def similarity_ratio(content1, content2):
    if not content1 or not content2:
        return 0.0

    matcher = difflib.SequenceMatcher(None, ''.join(content1), ''.join(content2))
    return matcher.ratio() * 100

def main():
    global similar_pairs, total_comparisons

    parser = argparse.ArgumentParser(description='Сравнение файлов на процентное совпадение')
    parser.add_argument('folder_path', help='Путь к папке для сканирования')
    parser.add_argument('-e', '--extension', default='.txt',
                       help='Расширение файлов для поиска (по умолчанию: .txt)')
    parser.add_argument('-a', action='store_true',
                       help='Сканировать ВСЕ файлы кроме исключенных')
    parser.add_argument('-x', action='append', default=[],
                       help='Исключить файлы с указанным расширением (можно несколько раз)')
    parser.add_argument('-v', action='store_true',
                       help='Подробный вывод процесса сравнения')
    parser.add_argument('-l', action='store_true',
                       help='Сравнивать ВСЕ файлы только с файлами из папок содержащих "LOC"')
    parser.add_argument('-o', '--output',
                       help='Вывод результатов в файл (по умолчанию: вывод в консоль)')
    args = parser.parse_args()

    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, args.output))

    if not os.path.exists(args.folder_path):
        print(f"Папка '{args.folder_path}' не существует")
        sys.exit(1)

    print("Сканируем папку...")

    if args.l:
        all_files = find_files(folder_path=args.folder_path,
                              extension=args.extension,
                              exclude_extensions=args.x,
                              all_files=args.a)
        loc_files = find_loc_files(folder_path=args.folder_path,
                                  extension=args.extension,
                                  exclude_extensions=args.x,
                                  all_files=args.a)

        mode_info = "все файлы" if args.a else f"расширение '{args.extension}'"
        exclude_info = f" (исключая: {', '.join(args.x)})" if args.x else ""

        print(f"Найдено {len(all_files)} файлов всего ({mode_info}{exclude_info})")
        print(f"Из них {len(loc_files)} файлов из папок LOC")

        if len(all_files) < 1 or len(loc_files) < 1:
            print("Недостаточно файлов для сравнения в режиме LOC")
            sys.exit(0)

        files_to_compare = all_files
        target_files = loc_files

    else:
        files_to_compare = find_files(folder_path=args.folder_path,
                                     extension=args.extension,
                                     exclude_extensions=args.x,
                                     all_files=args.a)
        target_files = None

        mode_info = "все файлы" if args.a else f"расширение '{args.extension}'"
        exclude_info = f" (исключая: {', '.join(args.x)})" if args.x else ""

        if len(files_to_compare) < 2:
            print(f"Найдено меньше 2 файлов ({mode_info}{exclude_info})")
            sys.exit(0)

        print(f"Найдено {len(files_to_compare)} файлов ({mode_info}{exclude_info})")

    print(f"\nНачинаем сравнение...")
    if args.l:
        print(f"Сравниваем {len(files_to_compare)} файлов с {len(target_files)} файлами из папок LOC")
    else:
        print(f"Сравниваем {len(files_to_compare)} файлов ({len(files_to_compare)*(len(files_to_compare)-1)//2} пар)")
    print("Ctrl+C для вывода промежуточных результатов")

    similar_pairs = []
    total_comparisons = 0

    try:
        if args.l:
            for file1 in files_to_compare:
                for file2 in target_files:
                    if file1 == file2:
                        continue

                    total_comparisons += 1

                    file1_name = os.path.basename(file1)
                    file2_name = os.path.basename(file2)

                    if args.v:
                        print(f"Сравниваем ({total_comparisons}): {file1_name} <-> {file2_name}", end=' ... ')
                        sys.stdout.flush()

                    content1 = read_file_content(file1)
                    content2 = read_file_content(file2)

                    similarity = similarity_ratio(content1, content2)

                    if args.v:
                        status = "сходство" if similarity >= 50.0 else "отличаются"
                        print(f"{similarity:6.1f}% {status}")

                    if similarity >= 50.0:
                        pair = (file1, file2) if file1 < file2 else (file2, file1)
                        similar_pairs.append((pair, similarity))
        else:
            for i in range(len(files_to_compare)):
                for j in range(i + 1, len(files_to_compare)):
                    total_comparisons += 1

                    file1_name = os.path.basename(files_to_compare[i])
                    file2_name = os.path.basename(files_to_compare[j])

                    if args.v:
                        print(f"Сравниваем ({total_comparisons}): {file1_name} <-> {file2_name}", end=' ... ')
                        sys.stdout.flush()

                    content1 = read_file_content(files_to_compare[i])
                    content2 = read_file_content(files_to_compare[j])

                    similarity = similarity_ratio(content1, content2)

                    if args.v:
                        status = "сходство" if similarity >= 50.0 else "отличаются"
                        print(f"{similarity:6.1f}% {status}")

                    if similarity >= 50.0:
                        pair = (files_to_compare[i], files_to_compare[j])
                        similar_pairs.append((pair, similarity))

    except KeyboardInterrupt:
        pass

    print_results(similar_pairs, total_comparisons, args.output)

if __name__ == "__main__":
    main()

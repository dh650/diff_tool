
# File Differences Tool

A lightweight and fast tool for automatic comparison of text files and visual display of the differences between them.


## Usage

```bash
diff_tool.py [-h] [-e EXTENSION] [-a] [-x X] [-v] [-l] folder_path

Сравнение файлов на процентное совпадение

positional arguments:
  folder_path           Путь к папке для сканирования

optional arguments:
  -h, --help            show this help message and exit
  -e EXTENSION, --extension EXTENSION
                        Расширение файлов для поиска (по умолчанию: .txt)
  -a                    Сканировать ВСЕ файлы кроме исключенных
  -x X                  Исключить файлы с указанным расширением (можно
                        несколько раз)
  -v                    Подробный вывод процесса сравнения
  -l                    Сравнивать ВСЕ файлы только с файлами из папок
                        содержащих "LOC"

```
## Example

```bash
python3 diff_tool.py -vla -x .yaml -x .tree -x .png -x .log -x .md -x .json -x .pdf -x .spec -x .xml -x .zip -x .gz -x .tar /path/to/db/folder/ -o result.txt
```

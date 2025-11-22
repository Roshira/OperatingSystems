#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <string.h>

#define BUF_SIZE 1024 // Розмір блоку для читання

void print_tail(int fd, int num_lines) {
    off_t file_size = lseek(fd, 0, SEEK_END);
    
    if (file_size == 0) return; // Порожній файл

    off_t current_pos = file_size;
    int lines_found = 0;
    char buf[BUF_SIZE];
    int target_newlines = num_lines;

    // --- Етап 1: Визначення кількості потрібних символів нового рядка ---
    // Хитрість: якщо файл закінчується на \n, то цей останній \n не починає новий рядок.
    // Нам треба знайти (N+1)-й символ \n з кінця, щоб почати друк одразу ПІСЛЯ нього.
    // Але якщо останній байт файлу НЕ \n, то достатньо знайти N символів \n.
    
    // Читаємо останній байт, щоб перевірити, чи є там \n
    if (file_size > 0) {
        lseek(fd, -1, SEEK_END);
        char last_char;
        if (read(fd, &last_char, 1) == 1) {
            if (last_char == '\n') {
                target_newlines = num_lines + 1;
            }
        }
    }

    // --- Етап 2: Читання файлу задом наперед ---
    // Ми рухаємось блоками (BUF_SIZE) від кінця до початку
    while (current_pos > 0) {
        size_t bytes_to_read = (current_pos >= BUF_SIZE) ? BUF_SIZE : current_pos;
        current_pos -= bytes_to_read;

        // Стрибаємо на нову позицію
        lseek(fd, current_pos, SEEK_SET);
        
        // Читаємо блок
        if (read(fd, buf, bytes_to_read) != bytes_to_read) {
            perror("Помилка читання");
            exit(1);
        }

        // Скануємо блок у зворотному напрямку (справа наліво)
        for (int i = bytes_to_read - 1; i >= 0; i--) {
            if (buf[i] == '\n') {
                lines_found++;
                
                if (lines_found == target_newlines) {
                    // Ми знайшли початок потрібного блоку!
                    // Дані починаються з наступного байту після цього \n
                    off_t start_print_pos = current_pos + i + 1;
                    lseek(fd, start_print_pos, SEEK_SET);
                    goto print_content;
                }
            }
        }
    }

    // Якщо ми дійшли до початку файлу і не знайшли достатньо рядків,
    // значить, треба друкувати весь файл.
    lseek(fd, 0, SEEK_SET);

print_content:
    // --- Етап 3: Вивід знайденої частини на екран ---
    while (1) {
        ssize_t bytes_read = read(fd, buf, sizeof(buf));
        if (bytes_read <= 0) break;
        write(STDOUT_FILENO, buf, bytes_read);
    }
}

int main(int argc, char *argv[]) {
    if (argc != 3 && argc != 4) {
        fprintf(stderr, "Використання: %s -n <кількість> <файл>\n", argv[0]);
        return 1;
    }

    int n = 0;
    char *filename = NULL;

    // Простий парсинг аргументів (підтримує "mytail -n 5 file" або "mytail -5 file")
    if (strcmp(argv[1], "-n") == 0) {
        n = atoi(argv[2]);
        filename = argv[3];
    } else if (argv[1][0] == '-') {
        // Випадок mytail -5 file
        n = atoi(argv[1] + 1); // Пропускаємо мінус
        filename = argv[2];
    } else {
        fprintf(stderr, "Невірний формат аргументів\n");
        return 1;
    }

    int fd = open(filename, O_RDONLY);
    if (fd < 0) {
        perror("Не вдалося відкрити файл");
        return 1;
    }

    print_tail(fd, n);

    close(fd);
    return 0;
}

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>
#include <unistd.h>

/*
 * Функція для рекурсивного обходу
 * base_path: шлях, де шукаємо
 * search_term: рядок, який шукаємо (або NULL, якщо виводимо все)
 * indent_level: рівень вкладеності для красивого відступу
 */
void find_recursive(const char *base_path, const char *search_term, int indent_level) {
    char path[1024];
    struct dirent *dp;
    DIR *dir = opendir(base_path);

    if (!dir) {
        return; // Пропускаємо папки, до яких немає доступу
    }

    while ((dp = readdir(dir)) != NULL) {
        // 1. Ігноруємо . та .. (захист від нескінченної рекурсії)
        if (strcmp(dp->d_name, ".") == 0 || strcmp(dp->d_name, "..") == 0) {
            continue;
        }

        // 2. Будуємо повний шлях
        snprintf(path, sizeof(path), "%s/%s", base_path, dp->d_name);

        // 3. ЛОГІКА ПОШУКУ
        // Ми показуємо файл, якщо:
        // а) search_term дорівнює NULL (режим "показати все")
        // б) Ім'я файлу містить search_term (використовуємо strstr)
        int is_match = 0;
        if (search_term == NULL) {
            is_match = 1;
        } else if (strstr(dp->d_name, search_term) != NULL) {
            is_match = 1;
        }

        // Виводимо тільки якщо є збіг
        if (is_match) {
            for (int i = 0; i < indent_level; i++) printf("  | ");
            printf("|- %s\n", dp->d_name);
        }

        // 4. Перевіряємо, чи це каталог, щоб піти вглиб
        // ВАЖЛИВО: Ми рекурсивно заходимо в папки НАВІТЬ якщо їхня назва
        // не співпала з пошуком. Адже шуканий файл може бути всередині!
        struct stat s;
        if (lstat(path, &s) == 0) {
            if (S_ISDIR(s.st_mode)) {
                find_recursive(path, search_term, indent_level + 1);
            }
        }
    }

    closedir(dir);
}

int main(int argc, char *argv[]) {
    char *start_path = ".";
    char *search_term = NULL;

    // --- Простий парсинг аргументів ---
    // Формати:
    // ./myfind
    // ./myfind <path>
    // ./myfind <path> -name <text>
    
    if (argc > 1) {
        // Якщо перший аргумент не починається з "-", вважаємо його шляхом
        if (argv[1][0] != '-') {
            start_path = argv[1];
        }
    }

    // Шукаємо прапорець -name серед аргументів
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-name") == 0) {
            if (i + 1 < argc) {
                search_term = argv[i + 1];
            } else {
                fprintf(stderr, "Помилка: після -name очікується рядок пошуку.\n");
                return 1;
            }
        }
    }

    printf("Пошук у '%s'", start_path);
    if (search_term) {
        printf(" (фільтр: '%s')", search_term);
    }
    printf(":\n");

    find_recursive(start_path, search_term, 0);

    return 0;
}

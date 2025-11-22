#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h> // Головна бібліотека для роботи з каталогами
#include <unistd.h>
#include <pwd.h>    // Для отримання імені власника (getpwuid)
#include <grp.h>    // Для отримання імені групи (getgrgid)
#include <time.h>   // Для форматування часу

// Функція для виводу детальної інформації (як ls -l)
void print_file_info(const char *path, const char *filename) {
    struct stat s;
    
    // Важливо: stat потребує ПОВНОГО шляху до файлу, а не просто імені
    if (stat(path, &s) < 0) {
        perror("stat failed");
        return;
    }

    // 1. Права доступу (наприклад, drwxr-xr-x)
    printf( (S_ISDIR(s.st_mode)) ? "d" : "-");
    printf( (s.st_mode & S_IRUSR) ? "r" : "-");
    printf( (s.st_mode & S_IWUSR) ? "w" : "-");
    printf( (s.st_mode & S_IXUSR) ? "x" : "-");
    printf( (s.st_mode & S_IRGRP) ? "r" : "-");
    printf( (s.st_mode & S_IWGRP) ? "w" : "-");
    printf( (s.st_mode & S_IXGRP) ? "x" : "-");
    printf( (s.st_mode & S_IROTH) ? "r" : "-");
    printf( (s.st_mode & S_IWOTH) ? "w" : "-");
    printf( (s.st_mode & S_IXOTH) ? "x" : "-");

    // 2. Кількість посилань
    printf(" %ld", s.st_nlink);

    // 3. Власник та Група (перетворюємо ID в імена)
    struct passwd *pw = getpwuid(s.st_uid);
    struct group  *gr = getgrgid(s.st_gid);
    printf(" %s %s", (pw) ? pw->pw_name : "unknown", (gr) ? gr->gr_name : "unknown");

    // 4. Розмір
    printf(" %5ld", s.st_size);

    // 5. Ім'я файлу
    printf(" %s\n", filename);
}

int main(int argc, char *argv[]) {
    char *dirname = "."; // За замовчуванням поточний каталог
    int list_long = 0;   // Прапор для -l

    // --- Розбір аргументів командного рядка ---
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-l") == 0) {
            list_long = 1;
        } else {
            dirname = argv[i];
        }
    }

    // --- Відкриття каталогу ---
    DIR *d = opendir(dirname);
    if (d == NULL) {
        perror("Не вдалося відкрити каталог");
        return 1;
    }

    struct dirent *dir;
    // --- Читання каталогу запис за записом ---
    while ((dir = readdir(d)) != NULL) {
        // Якщо потрібен простий вивід
        if (!list_long) {
            printf("%s\n", dir->d_name);
        } 
        // Якщо потрібен детальний вивід (-l)
        else {
            char fullpath[1024];
            // Склеюємо шлях до папки + ім'я файлу
            // Наприклад: "." + "/" + "file.txt"
            snprintf(fullpath, sizeof(fullpath), "%s/%s", dirname, dir->d_name);
            
            print_file_info(fullpath, dir->d_name);
        }
    }

    closedir(d);
    return 0;
}

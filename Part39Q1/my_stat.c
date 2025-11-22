#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    // 1. Перевіряємо, чи передав користувач ім'я файлу
    if (argc != 2) {
        fprintf(stderr, "Використання: %s <файл_або_каталог>\n", argv[0]);
        return 1;
    }

    // 2. Оголошуємо структуру stat для зберігання даних
    struct stat s;

    // 3. Викликаємо системний виклик stat
    // argv[1] - це шлях до файлу, переданий з командного рядка
    if (stat(argv[1], &s) < 0) {
        perror("Помилка виклику stat"); // Виведе причину помилки (напр., "No such file")
        return 1;
    }

    // 4. Виводимо отриману інформацію
    printf("Інформація для '%s':\n", argv[1]);
    printf("---------------------------\n");
    printf("Розмір файлу: \t\t%ld байт\n", s.st_size);
    printf("Кількість блоків: \t%ld\n", s.st_blocks);
    printf("Кількість посилань (Links): %ld\n", s.st_nlink);
    printf("Номер inode: \t\t%ld\n", s.st_ino);
    
    // Маска & 0777 потрібна, щоб відкинути службові біти і залишити тільки права доступу
    printf("Права доступу: \t\t%o\n", s.st_mode & 0777); 

    return 0;
}

# Описание проекта:  
# Социальная сеть для блогеров



**Как пользоватся**:  
Клонировать репозиторий и перейти в него в командной строке:

```
git clone 
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

* Если у вас Linux/MacOS

    ```
    source venv/bin/activate
    ```

* Если у вас windows

    ```
    source venv/scripts/activate
    ```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Запустить миграции в директории с файлом manage.py
```
python manage.py migrate
```

Собрать статику
```
python manage.py collectstatic
```
Запустить приложение
```
python manage.py runserver
```


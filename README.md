# smart-light-switch

Wi-Fi актуатор для звичайного настінного вимикача: **ESP32 + металева серва (25T) + 3D-друкований корпус**.
Серва натискає клавішу, а потім повертається в нейтраль, тому вимикачем можна користуватись і руками.

- Веб-інтерфейс на ESP32: `http://switch.local` (iPhone / ПК, є PWA-іконка)
- Налаштування кутів `0°..360°`, швидкість, час дотиску, перезавантаження — у шестерні
- Автоперепідключення Wi-Fi + запасна точка доступу `SmartSwitch-ESP32` (`192.168.4.1`)
- **Бездротова прошивка (OTA)** через GitHub Actions на self-hosted runner

## Структура
| Шлях | Що |
|---|---|
| `src/main.cpp` | прошивка + веб-UI |
| `src/secrets.example.h` | шаблон секретів (`secrets.h` не комітиться) |
| `cad/generate_stl.py` | параметричний генератор STL (корпус, Т-насадка, кришка, фіксатор серви) |
| `cad/*.stl` | готові моделі |
| `docs/switch_dimensions.html` | креслення з усіма розмірами |
| `assets/` | іконка застосунку |

## Перший запуск
```bash
cp src/secrets.example.h src/secrets.h   # впиши Wi-Fi та OTA-пароль
make flash                               # один раз по USB
```
Далі `make ota` або просто `git push` (див. нижче).

## CI/CD: комміт -> прошивка по повітрю
Workflow `.github/workflows/ota.yml` на кожен push у `main`, який чіпає `src/`, `platformio.ini` або сам workflow:
1. збирає прошивку PlatformIO,
2. заливає її в ESP32 по Wi-Fi (`espota` -> `switch.local`),
3. перевіряє `GET /api/sys`.

Хмарні раннери GitHub не бачать локальну мережу, тому потрібен **self-hosted runner** на машині в тій самій Wi-Fi.

### Налаштування runner
1. Repo -> Settings -> Actions -> Runners -> New self-hosted runner (Linux x64).
2. Запусти `./config.sh --url https://github.com/DeltaEngineering-Students/smart-light-switch --token <TOKEN> --labels smartswitch`.
3. Покласти секрети на runner-машину: `~/.config/smartswitch/secrets.h` (копія `src/secrets.h`).
4. `sudo ./svc.sh install && sudo ./svc.sh start`.

> **Безпека.** Репозиторій публічний, а self-hosted runner виконує код на твоєму ПК. Тому workflow запускається лише на `push` власника (не на `pull_request`), а в Settings -> Actions -> General варто поставити *Require approval for all outside collaborators*.

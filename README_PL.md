# PlaySched – Harmonogram Odtwarzania Playlist Spotify

[![Licencja: MIT](https://img.shields.io/badge/Licencja-MIT-żółty.svg)](https://opensource.org/licenses/MIT)

![Ikona Aplikacji](static/android-chrome-192x192.png)

[Historia Wersji](VERSION.md) – Aktualna Wersja: v0.3.0 – 14 maja 2026

[Plan Rozwoju](ROADMAP.md)

Projekt łączący aplikację webową do planowania odtwarzania playlist Spotify z narzędziem wiersza poleceń do bezpośredniej kontroli Spotify, zarządzania historią i synchronizacji danych.

Aplikacja będzie się rozwijać z czasem. Obecnie rozwiązuje jeden konkretny problem – zdałem sobie sprawę, że jedynym powodem, dla którego używam Amazon Alexy™, jest odtwarzanie/zatrzymywanie muzyki o określonych godzinach (i w określone dni). Interfejs Alexy do tego celu jest okropny. Teraz mogę odłączyć Alexę i używać znacznie lepszych głośników w laptopie za pośrednictwem aplikacji Spotify, sterowanej przez tę aplikację harmonogramu. Zobacz [Plan Rozwoju](ROADMAP.md), aby dowiedzieć się, co może pojawić się w przyszłości. Może. Jeśli nie zacznę się rozpraszać innymi błyszczącymi rzeczami, teraz gdy ten konkretny problem został rozwiązany.

## Przegląd

* **Aplikacja Webowa (`playsched.py`):** Zapewnia przyjazny interfejs webowy do planowania odtwarzania playlist Spotify na konkretnych urządzeniach o ustalonych porach. Obejmuje opcje powtarzalności (dni tygodnia), godziny startu/stopu, głośność i tryb losowy. Pozwala zarządzać utworzonymi harmonogramami (edycja, duplikowanie, pauza, usuwanie).
* **Skrypt Wiersza Poleceń (`play_spotify_playlist.py`):** Oferuje bezpośrednią interakcję z terminalem ze Spotify: listowanie urządzeń/playlist, uruchamianie odtwarzania, zarządzanie lokalną bazą danych historii odtwarzania, synchronizowanie wszystkich playlist i utworów lokalnie oraz eksportowanie tych danych.

## Funkcje

### Funkcje Aplikacji Webowej (`playsched.py`)

* **Uwierzytelnianie Spotify:** Bezpieczne logowanie za pomocą konta Spotify (OAuth 2.0). Tokeny są teraz przechowywane w bazie danych SQLite (tabela `user_tokens`), co umożliwia obsługę wielu użytkowników i eliminuje konflikty pliku cache.
* **Przeglądanie Playlist:** Przeglądanie i filtrowanie playlist Spotify.
* **Lista Urządzeń:** Automatyczne wykrywanie dostępnych urządzeń Spotify Connect.
* **Harmonogramowanie:**
    * Wybierz playlistę i docelowe urządzenie.
    * Ustaw godzinę startu (GG:MM) i opcjonalną godzinę stopu (GG:MM).
    * Określ dni tygodnia dla harmonogramów cyklicznych (lub zostaw puste dla jednorazowego odtwarzania).
    * Ustaw głośność odtwarzania (opcjonalnie).
    * Włącz/wyłącz tryb losowy dla odtwarzania.
    * Określ strefę czasową harmonogramu.
* **Zarządzanie Harmonogramami:**
    * Przeglądaj wszystkie utworzone harmonogramy, posortowane według czasu następnego uruchomienia.
    * Ręcznie uruchom odtwarzanie ("Odtwórz Teraz").
    * Zatrzymaj odtwarzanie natychmiastowo ("Zatrzymaj Teraz").
    * Wstrzymaj/wznów harmonogramy (przełączanie stanu aktywnego).
    * Edytuj istniejące harmonogramy.
    * Duplikuj istniejące harmonogramy, aby łatwo tworzyć warianty.
    * Usuwaj harmonogramy.
* **Widget Teraz Gra:** Dynamiczne wyświetlanie aktualnie odtwarzanego utworu (tytuł, wykonawca, okładka albumu, pasek postępu z czasem), nazwy aktywnego urządzenia oraz następnego utworu w kolejce. Odświeża się automatycznie co 5 sekund.
* **Zegar na Żywo:** Aktualna data i godzina wyświetlane wyraźnie w nagłówku, z sekundowym odświeżaniem i czytelną czcionką monospace.
* **Motyw Ciemny:** Pełny przełącznik motywu ciemnego/jasnego z wykrywaniem preferencji systemowych i zapisywaniem w `localStorage`.
* **Powiadomienia Toast:** Nieinwazyjne komunikaty sukcesu/info zamiast blokujących popupów `alert()`.
* **Harmonogram w Tle:** Używa APScheduler do automatycznego uruchamiania/zatrzymywania odtwarzania zgodnie z zdefiniowanymi harmonogramami.

### Funkcje Skryptu Wiersza Poleceń (`play_spotify_playlist.py`)

* **Lista Urządzeń:** Wyświetla dostępne urządzenia Spotify Connect.
* **Lista Playlist:** Pokazuje playlisty bezpośrednio ze Spotify.
* **Kontrola Odtwarzania:** Rozpocznij odtwarzanie określonej playlisty na wybranym urządzeniu bezpośrednio z wiersza poleceń.
* **Historia Odtwarzania:**
    * Pobiera ostatnio odtwarzane utwory ze Spotify.
    * Przechowuje tę historię w lokalnej bazie danych SQLite.
    * Wyświetla ostatnio odtwarzane playlisty na podstawie zapisanej historii (z konwersją na lokalny czas).
* **Pełna Synchronizacja Playlist:**
    * Pobiera wszystkie playlisty (utworzone i obserwowane) oraz ich utwory ze Spotify.
    * Przechowuje te dane w lokalnych tabelach SQLite (`synced_playlists`, `synced_playlist_tracks`).
    * Oznacza playlisty lub utwory jako "usunięte", jeśli nie są już znalezione w bibliotece Spotify, bez usuwania ich z bazy danych.
* **Eksport Danych:**
    * Eksportuje zsynchronizowane playlisty i utwory z lokalnej bazy danych.
    * Wspiera eksport do Excela (`.xlsx` z osobnymi arkuszami dla playlist i utworów), CSV (generuje dwa pliki: `*_playlists.csv` i `*_tracks.csv`) lub JSON (`.json` ze strukturą danych).
* **Obsługa Wielu Użytkowników (DB):** CLI wymaga argumentu `--user-id`. Tokeny są pobierane ze wspólnej bazy danych (wypełnionej przez logowanie w aplikacji webowej).

![Przeglądanie Playlist](img/screenshot-browse-playlists.jpg)

![Harmonogram Playlisty](img/screenshot-schedule.jpg)

![Przeglądanie i Aktualizacja Playlist](img/screenshot-view-update.jpg)

## Wymagania Wstępne

* **Python:** Zalecana wersja 3.8 lub wyższa.
* **pip lub conda:** Do instalacji pakietów.
* **OpenSSL:** Wymagany do generowania certyfikatów (zazwyczaj preinstalowany na Linux/macOS, do pobrania dla Windows).
* **Konto Spotify:** Zwykłe lub Premium.
* **Dane Aplikacji Spotify Developer:** Musisz zarejestrować aplikację w Spotify Developer Dashboard, aby uzyskać klucze API. Szczegółowe kroki poniżej.
* **Dla Funkcji Eksportu:** Biblioteki Pythona `pandas` i `openpyxl` (zobacz sekcję Instalacja w `requirements.txt`).

### Konfiguracja Aplikacji Spotify Developer

Aby umożliwić tej aplikacji interakcję z Twoim kontem Spotify, musisz ją zarejestrować na platformie deweloperskiej Spotify:

1.  **Przejdź do Spotify Developer Dashboard:** Otwórz [https://developer.spotify.com/dashboard/](https://developer.spotify.com/dashboard/) w przeglądarce.
2.  **Zaloguj się:** Użyj swoich danych logowania do konta Spotify.
3.  **Utwórz Aplikację:** Kliknij **"Create App"** (lub "Create an app"), wypełnij nazwę i opis, zaakceptuj warunki i kliknij **"Create"**.
4.  **Pobierz Dane Logowania:** Na pulpicie aplikacji skopiuj swój **Client ID**. Kliknij **"Show client secret"**, aby wyświetlić i skopiować swój **Client Secret**. Zachowaj sekret w poufności.
5.  **Skonfiguruj Ustawienia:** Kliknij **"Edit Settings"** (lub znajdź sekcję ustawień dla swojej aplikacji).
    * **Website:** Musisz podać adres URL strony. Dla lokalnego rozwoju możesz użyć lokalizacji serwera Flask (np. `https://127.0.0.1:9093`).
    * **Redirect URIs:** Dodaj dokładny URI, którego aplikacja użyje do callbacków. Dla tego projektu używającego HTTPS na domyślnym porcie `9093`, dodaj:
        ```
        https://127.0.0.1:9093/callback
        ```
        * Użyj `127.0.0.1` zamiast `localhost` – localhost może czasem powodować problemy z walidacją callbacków lub politykami bezpieczeństwa przeglądarki.
        * Upewnij się, że to **dokładnie pasuje** do `SPOTIPY_REDIRECT_URI` w Twoim pliku `.env`. Dodaj jeden URI na linię.
    * Kliknij **"Save"** na dole strony ustawień.
6.  **Użyj Danych Logowania:** Skopiuj Client ID i Client Secret do pliku `.env`.

## Instalacja

1.  **Sklonuj Repozytorium:**
    ```bash
    git clone https://github.com/dkoryto/playsched
    cd playsched
    ```

2.  **Utwórz Środowisko Wirtualne (Zalecane):**

    * **Używając `venv` (standardowy Python):**
        ```bash
        # Utwórz środowisko (uruchom raz)
        python -m venv venv

        # Aktywuj środowisko
        # Na Windows (cmd/powershell):
        .\venv\Scripts\activate
        # Na macOS/Linux (bash/zsh):
        source venv/bin/activate
        ```

    * **Używając `conda`:**
        ```bash
        # Utwórz środowisko (uruchom raz)
        conda create -n spotify-scheduler python=3.9

        # Aktywuj środowisko
        conda activate spotify-scheduler
        ```

3.  **Zainstaluj Zależności:**
    Upewnij się, że Twoje środowisko wirtualne jest aktywowane.
    ```bash
    pip install -r requirements.txt
    ```

## Konfiguracja (Plik `.env`)

Aplikacja używa zmiennych środowiskowych ładowanych z pliku `.env` w głównym katalogu projektu.

1.  Utwórz plik o nazwie `.env` w głównym katalogu projektu. Jest przykładowy plik `.env-sample`, który możesz skopiować jako szablon.
2.  Dodaj następujące zmienne, zastępując wartości placeholderów swoimi rzeczywistymi danymi logowania i preferowanymi ustawieniami:

    ```dotenv
    # Dane Spotify API (Wymagane)
    SPOTIPY_CLIENT_ID='TWÓJ_SPOTIFY_CLIENT_ID'
    SPOTIPY_CLIENT_SECRET='TWÓJ_SPOTIFY_CLIENT_SECRET'
    SPOTIPY_REDIRECT_URI='https://127.0.0.1:9093/callback'

    # Konfiguracja Flask (Wymagane)
    SECRET_KEY='TWÓJ_SILNY_LOSOWY_KLUCZ'
    FLASK_DEBUG=1

    # Ustawienia Wspólne (Wymagane)
    SCHEDULE_DB_FILE='playsched.db'
    # PRZESTARZAŁE: SPOTIPY_CACHE_PATH nie jest już używane przez aplikację webową ani scheduler.
    # Tokeny są teraz przechowywane w bazie danych (tabela user_tokens).
    # SPOTIPY_CACHE_PATH='.spotify_token_cache.json'
    SCHEDULER_INTERVAL_SECONDS=15
    SCHEDULER_TIMEZONE='UTC'

    # Certyfikaty SSL dla HTTPS
    # FLASK_CERT_FILE=localhost.crt
    # FLASK_KEY_FILE=localhost.key
    ```

## HTTPS dla Lokalnego Rozwoju

Spotify API wymaga `https://` dla URI callbacków. Serwer deweloperski Flask musi być skonfigurowany do używania HTTPS.

**Opcja 1: Użycie Niestandardowych Certyfikatów (Zalecane)**

1.  **Wygeneruj Certyfikaty:**
    ```bash
    chmod +x generate_certs.zsh
    zsh generate_certs.zsh
    ```
    Tworzy to `myCA.pem` (certyfikat CA), `localhost.crt` (certyfikat serwera) i `localhost.key` (klucz serwera).

2.  **Zaufaj Swemu Certyfikatowi CA (`myCA.pem`):**
    * **Chrome:**
        * Przejdź do `chrome://settings/certificates`.
        * Zakładka **"Authorities"**.
        * Kliknij **"Import..."**.
        * Wybierz wygenerowany plik `myCA.pem`.
        * Zaznacz **"Trust this certificate for identifying websites"**.
        * Kliknij OK/Finish.
    * **macOS:**
        * Zaimportuj `myCA.pem` przez Keychain Access.
        * Znajdź zaimportowany certyfikat, kliknij dwukrotnie.
        * Rozwiń sekcję **Trust** i ustaw "When using this certificate:" na **"Always Trust"**.
    * **Windows:** Wyszukaj "Manage computer certificates", uruchom jako administrator. Przejdź do "Trusted Root Certification Authorities" > "Certificates". Zaimportuj `myCA.pem`.

3.  **Skonfiguruj Flask:** Dodaj do `.env`:
    ```dotenv
    FLASK_CERT_FILE=localhost.crt
    FLASK_KEY_FILE=localhost.key
    ```

4.  **Dostęp:** Przejdź do `https://localhost:9093` lub `https://127.0.0.1:9093`. Nie powinieneś widzieć ostrzeżenia o bezpieczeństwie, jeśli CA został zaufany.

**Opcja 2: Automatyczne Certyfikaty 'adhoc'**

1.  Upewnij się, że `pyOpenSSL` jest zainstalowany (`pip install pyOpenSSL`).
2.  **Nie ustawiaj** `FLASK_CERT_FILE` i `FLASK_KEY_FILE` w `.env` (zakomentuj je).
3.  Uruchom aplikację. Przejdź do `https://127.0.0.1:9093`. Przeglądarka pokaże ostrzeżenie – kliknij "Advanced" i wybierz kontynuowanie.

## Uruchamianie Aplikacji

### Uruchamianie Aplikacji Webowej

```bash
python playsched.py
```

Otwórz przeglądarkę i przejdź do `https://127.0.0.1:9093`.

**Zaloguj się przez Spotify** w interfejsie webowym. To zapisze token uwierzytelniania w bazie danych (tabela `user_tokens`), udostępniając go schedulerowi i CLI.

### Uruchamianie Skryptu Wiersza Poleceń

CLI pobiera teraz tokeny z bazy danych (nie z pliku cache). Musisz zalogować się przez aplikację webową przynajmniej raz przed użyciem komend CLI wymagających autoryzacji Spotify.

```bash
# Lista użytkowników z zapisanymi tokenami
python play_spotify_playlist.py --list-users

# Przykład: lista urządzeń
python play_spotify_playlist.py --user-id TWÓJ_USER_ID --list-devices
```

## Użytkowanie

### Użytkowanie Aplikacji Webowej

1.  **Logowanie:** Przejdź do adresu aplikacji i kliknij "Login with Spotify". Autoryzuj aplikację przez stronę Spotify.
2.  **Przeglądaj/Harmonogramuj:** Użyj zakładki "My Playlists", aby znaleźć playlisty. Kliknij "Schedule", aby otworzyć formularz.
3.  **Wypełnij Formularz:** Wybierz urządzenie, dni, godziny, głośność, tryb losowy i strefę czasową. Kliknij "Save Schedule".
4.  **Zarządzaj:** Użyj zakładki "Scheduled Playlists", aby przeglądać, odtwarzać teraz, zatrzymywać, wstrzymywać/wznawiać, edytować, duplikować lub usuwać harmonogramy.

### Użytkowanie Skryptu Wiersza Poleceń

Wszystkie akcje wymagające autoryzacji Spotify potrzebują `--user-id`.

* **Lista dostępnych urządzeń:**
    ```bash
    python play_spotify_playlist.py --user-id TWÓJ_USER_ID --list-devices
    ```
* **Lista playlist:**
    ```bash
    python play_spotify_playlist.py --user-id TWÓJ_USER_ID --list-playlists
    ```
* **Aktualizacja lokalnej historii odtwarzania:**
    ```bash
    python play_spotify_playlist.py --user-id TWÓJ_USER_ID --update-history
    ```
* **Ostatnio odtwarzane playlisty z lokalnej bazy:**
    ```bash
    python play_spotify_playlist.py --user-id TWÓJ_USER_ID --recent-playlists
    ```
* **Synchronizuj wszystkie playlisty do lokalnej bazy:**
    ```bash
    python play_spotify_playlist.py --user-id TWÓJ_USER_ID --sync-playlists
    ```
* **Eksportuj zsynchronizowane dane:**
    ```bash
    # Eksport do Excela
    python play_spotify_playlist.py --export-data moje_dane_spotify.xlsx

    # Eksport do CSV
    python play_spotify_playlist.py --export-data moje_dane_spotify.csv

    # Eksport do JSON
    python play_spotify_playlist.py --export-data moje_dane_spotify.json
    ```
    *Uwaga: Eksport nie wymaga `--user-id`, ponieważ czyta tylko z lokalnej bazy danych.*
* **Odtwórz playlistę na konkretnym urządzeniu:**
    ```bash
    python play_spotify_playlist.py --user-id TWÓJ_USER_ID --device "Moje Głośniki" --playlist "Chill Mix"
    ```

## Rozwiązywanie Problemów (Troubleshooting)

### Problemy z Aplikacją Webową / Logowaniem

| Objaw | Przyczyna | Rozwiązanie |
|-------|-----------|-------------|
| `SpotifyOAuth initialized...` logowane wielokrotnie | Normalny log przy starcie, nie błąd | Zignoruj |
| „Authentication failed" lub pętla przekierowań po logowaniu | Niezgodność `SPOTIPY_REDIRECT_URI` | Upewnij się, że dokładnie pasuje do Redirect URI w Spotify Dashboard (wraz z `https://` i `/callback`) |
| Przeglądarka pokazuje „Your connection is not private" | Nietrustowany certyfikat self-signed | Zaufaj `myCA.pem` w przeglądarce (patrz sekcja HTTPS) lub użyj trybu adhoc i kliknij „Proceed" |
| Scheduler nie uruchamia odtwarzania | Brak tokena w DB dla użytkownika | Zaloguj się przez aplikację webową. Sprawdź `--list-users` w CLI, aby zweryfikować istnienie tokena |
| Scheduler nie uruchamia odtwarzania | Urządzenie offline / nieaktywne | Upewnij się, że Spotify jest otwarte na docelowym urządzeniu i pojawia się na liście urządzeń |
| „Error: Could not set volume" | Urządzenie nie obsługuje kontroli głośności | Sprawdź, czy urządzenie to głośnik Spotify Connect, a nie web player |

### Problemy z CLI

| Objaw | Przyczyna | Rozwiązanie |
|-------|-----------|-------------|
| `Error: --user-id is required` | CLI teraz wymaga jawnego user ID | Zaloguj się przez aplikację webową, potem uruchom `--list-users`, aby znaleźć swój ID |
| `No token found in database for user '...'` | Użytkownik nie zalogował się przez aplikację webową | Otwórz aplikację webową i kliknij „Login with Spotify" |
| `Error refreshing token...` | Refresh token unieważniony lub wygasł | Zaloguj się ponownie przez aplikację webową, aby wygenerować nowe tokeny |
| `No active Spotify devices found` | Spotify nie działa na docelowym urządzeniu | Otwórz Spotify na urządzeniu, na którym chcesz odtwarzać |
| Eksport kończy się błędem pandas | Brak opcjonalnych zależności | Uruchom `pip install pandas openpyxl` |

### Problemy z Bazą Danych / Plikami

| Objaw | Przyczyna | Rozwiązanie |
|-------|-----------|-------------|
| `Database tables checked/created.` | Normalny log przy pierwszym uruchomieniu | Zignoruj |
| Plik `.cache` się pojawia | Legacy cache Spotipy | Bezpiecznie usunąć. Dodaj `.cache` do `.gitignore` |
| Plik `.spotify_token_cache.json` nadal istnieje | Pozostałość po v0.2.x | Bezpiecznie usunąć po jednokrotnym zalogowaniu przez aplikację webową (tokeny są teraz w DB) |

### Problemy z Schedulerem / Zadaniami w Tle

| Objaw | Przyczyna | Rozwiązanie |
|-------|-----------|-------------|
| Harmonogram uruchamia się wielokrotnie na minutę | `SCHEDULER_INTERVAL_SECONDS` jest zbyt niskie, a zadanie trwa dłużej niż interwał | Domyślne 15s jest w porządku; sprawdź logi pod kątem czasu trwania zadania |
| „Skipping pause - playback is active, but not on target device" | Niezgodność ID urządzenia lub użytkownik zmienił urządzenie | Upewnij się, że zaplanowane ID urządzenia pasuje do aktualnie aktywnego urządzenia |
| Niezgodność stanu shuffle w logach | Eventual consistency API Spotify | Ostrzeżenie kosmetyczne; odtwarzanie działa poprawnie |

## Uwagi i Ograniczenia

* **Limity API Spotify:** Intensywne użytkowanie może potencjalnie przekroczyć limity API Spotify.
* **Dostępność Urządzenia:** Odtwarzanie wymaga, aby docelowe urządzenie było online i aktywne w Spotify. Akcje zawiodą, jeśli urządzenie jest niedostępne.
* **Precyzja Harmonogramu:** Zaplanowane zadania uruchamiają się na podstawie `SCHEDULER_INTERVAL_SECONDS`. Odtwarzanie może rozpocząć/zatrzymać się nieznacznie po dokładnej zaplanowanej minucie.
* **Strefy Czasowe i DST:** Upewnij się, że używasz prawidłowych nazw stref czasowych (nazwy bazy TZ). Backend używa `pytz` do obsługi stref czasowych i DST.
* **Przechowywanie Tokenów:** Tokeny uwierzytelniania są przechowywane w tabeli `user_tokens` w SQLite (wewnątrz `SCHEDULE_DB_FILE`). Scheduler i CLI odczytują z tej tabeli. Stary plik `.spotify_token_cache.json` nie jest już używany przez główną aplikację.
* **Bazy Danych:** `playsched.db` przechowuje harmonogramy aplikacji webowej, tokeny użytkowników, historię CLI oraz zsynchronizowane playlisty/utwory. Wykonuj kopie zapasowe, jeśli potrzebujesz.

## Wkład w Projekt

Wkłady są mile widziane! Zapraszamy do zgłaszania Pull Requestów lub otwierania Issues.

## Licencja

Ten projekt jest licencjonowany na licencji MIT – zobacz plik [LICENSE](LICENSE) dla szczegółów.

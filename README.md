# O Zelador do Vacuo -- C++/SDL2

## Dependencias

### Linux (Bazzite/Fedora)
```bash
sudo dnf install SDL2-devel SDL2_ttf-devel cmake gcc-c++
```

### Windows (vcpkg)
```bash
vcpkg install sdl2 sdl2-ttf
cmake -B build -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake
```

### Windows (MSYS2/MinGW)
```bash
pacman -S mingw-w64-x86_64-SDL2 mingw-w64-x86_64-SDL2_ttf cmake
```

## Fonte (obrigatoria)

Crie a pasta `assets/` na raiz do projeto e coloque uma fonte
monospace TTF com o nome `monospace.ttf`.

Sugestoes gratuitas:
- [JetBrains Mono](https://www.jetbrains.com/lp/mono/)
- [Source Code Pro](https://fonts.google.com/specimen/Source+Code+Pro)
- Ou use a DejaVu Mono do sistema (o codigo faz fallback automatico)

Se nao colocar nenhuma fonte, o jogo tenta usar as do sistema automaticamente.

## Build

### Linux
```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
./ZeladorDoVacuo
```

### Windows (Visual Studio)
```bash
mkdir build && cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake
cmake --build . --config Release
Release\ZeladorDoVacuo.exe
```

### Windows (MinGW)
```bash
mkdir build && cd build
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
mingw32-make
ZeladorDoVacuo.exe
```

## Estrutura do projeto

```
zelador_vacuo/
├── CMakeLists.txt
├── assets/
│   └── monospace.ttf        <- voce coloca aqui
├── include/
│   ├── managers/
│   │   ├── GameManager.hpp
│   │   ├── SanityManager.hpp
│   │   ├── DayManager.hpp
│   │   └── MaintenanceManager.hpp
│   └── systems/
│       ├── RadioSystem.hpp
│       └── RadarSystem.hpp
└── src/
    ├── main.cpp
    ├── managers/
    │   ├── GameManager.cpp
    │   ├── SanityManager.cpp
    │   ├── DayManager.cpp
    │   └── MaintenanceManager.cpp
    └── systems/
        ├── RadioSystem.cpp
        └── RadarSystem.cpp
```

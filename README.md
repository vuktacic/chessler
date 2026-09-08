# chessler/chessbot
A robot that plays chess. It uses a camera to detect Aruco tags on the board corners and the pieces, and an electromagnet on a gantry under the board to move the pieces. Designed for Hack Club's Outpost program. I wanted to do something involving Aruco tags outside of FRC, and this seemed like a good project to make.

## Structure
- [./assets](./assets): Repo images
- [./cad](./cad): 3d models
- [./core](./core): esp32 firmware
- [./pcb](./pcb): Kicad design files.
- [./vision](./vision): Computer side vision code
- [./bom.csv](./bom.csv): Bill of materials
- [./po.csv](./po.csv): Purchase order
- [./JOURNAL.md](./JOURNAL.md): Project journal


View the PCB on KiCanvas:  
[![View PCB on KiCanvas](https://hack.club/pcb-badge)](https://kicanvas.org/?github=https://github.com/vuktacic/chessler/tree/main/pcb)


## CAD

![alt text](./assets/image%20copy%2051.png)
![alt text](./assets/image%20copy%2052.png)
![alt text](./assets/image%20copy%2053.png)

## Schematic

![Schematic](./assets/schematic.png)

## PCB
![PCB front](./assets/image%20copy%2030.png)
![PCB back](./assets/image%20copy%2031.png)
![PCB assembly](./assets/image%20copy%2032.png)
![PCB detail](./assets/image%20copy%2033.png)

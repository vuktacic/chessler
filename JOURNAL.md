# chessler Journal

## June 13th, 2026
New project time!
![](./assets/image.png)

I've been thinking about this one for a couple days. It's a chess playing robot. My original idea was to have a gantry, but after deliberation I realized that an under the board design would be more compact, cleaner, and cheaper.

I would use a camera to detect the pieces. Object detection can be quite hard, but I realized that I can just attach pieces of coloured paper to the tops of the pieces, and then just use colour detection to find the pieces.

I started sourcing parts from aliexpress.
![](./assets/image%20copy.png)

I'm using MGN12 rails, which use M3 hardware which I already have.

I also found a nice tiny electromagnet:
![](./assets/image%20copy%202.png)

It's 20mm wide and 15mm thick with 30N of holding force.

About the magnet, I needed to make sure that it would be strong enough to drag pieces, but not so strong that it would pick up pieces unintendedly. (Picking up *A* piece is way easier than picking up *ONE* piece). I did some back of the napkin calculations and found that magnetic force generally dissipiates by 1/r^4. Meaning that the force of the electromagnet on side pieces is <1% of the force of a centered piece. (Assuming 6mm thick MDF and 45mm center to center piece distance).

I picked up some other things, like a bigger Nema 17 motor, M3 t-nuts, M5 brackets, extrusion, and optical endstops.
![](./assets/image%20copy%203.png)

I then hopped into fusion and started designing this.

Funny thing, I actually have quite a lot of experience designing with Aluminum extrusion. I did it all the time for FRC, and man I hated it. I really thought I escaped it!

However, when you can actually source proper components for it, it's pretty nice!

![](./assets/image%20copy%204.png)

I made the X axis belt run over the side extrusion, and started designing the gantry to hold the motor and clamp onto the belt. Lowkey, I don't really anticipate this taking too much time—most of it was spent sourcing parts. Tomorrow I'll have a lot of time to cad out the rest of the project, and then refine the tiny details and total the parts. After that, I'll start making the PCB for it.

Time today: 4.0 hours
**Time total: 4.0 hours**
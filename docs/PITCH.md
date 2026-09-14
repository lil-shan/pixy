# Pixy — pitches

## One line (Hackster summary field, bios, tweets)

A handheld STEM console where you have to earn the arcade: solve engineering
puzzles on a 64×32 LED matrix to bank Charge, then spend it on Breakout, Pong
and Snake.

## Ten seconds (someone walks up to the table)

> It's a games console for kids where the games are locked. You unlock them by
> solving engineering puzzles — logic gates, gear ratios, Ohm's law. Solve one,
> earn Charge. Charge buys Pong.

Then hand it to them. The object sells itself faster than any sentence.

## Thirty seconds (a judge, a teacher, a parent)

> Most STEM toys pick a side. Either they teach and feel like homework, or they
> entertain and the learning is a thin coat of paint.
>
> Pixy makes the learning the power source. Every puzzle you solve pays Charge,
> and Charge is the only way into the arcade. A kid who wants to play Pong gets
> there by working out gear ratios.
>
> Two things make it actually work. It **explains when you're wrong** — a wrong
> answer tells you *why* in one line, then puts you back on the same problem.
> And difficulty **adapts per subject, not globally** — so a kid who has binary
> cold but finds ratios hard gets hard binary and gentle ratios at the same
> time. One slider could never do that.
>
> It's two wireless units on an Arduino UNO Q: the handheld runs every game in
> Python on the Linux side, while the STM32 reads the controls at 1 kHz.

## For an Arduino UNO Q audience (why this board)

> Pixy uses both of the UNO Q's brains on the critical path, which is the whole
> argument for the board. The STM32 scans the control deck at 1 kHz — quadrature
> decoding and debounce need a jitter-free loop, and Linux userspace has no
> real-time guarantee. The Linux side runs every game in Python with Pillow,
> which is what makes six learning games and an adaptive difficulty engine a
> weekend of work instead of a month.
>
> The one thing neither half can do is drive a HUB75 panel — that needs DMA or a
> dedicated real-time core, and Protomatter has no STM32U5 backend. So that one
> job is offloaded to a XIAO over WiFi, at 114 fps. The ESP32 holds no game
> logic at all; it's a display adapter.

## The line to end on

> The arcade is the reward, but the point is that a kid works out a gear ratio
> to get there — and if they get it wrong, the console tells them why.

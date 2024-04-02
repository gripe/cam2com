import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import rc
rc('animation', html='jshtml')
#number of elements
theta = np.linspace(-math.pi, math.pi, 1000)

def amp_plot(f, d, a, delay, N):
  #   A = sin(pi*a.*sind(theta)/lambda);
  # B = pi*a.*sind(theta)/lambda;
  # C = ((2*pi*d.*sind(theta)/lambda)+phi);
  # D = sin((N/2).*C);
  # E = sin(C);
  # I = ((A./B).^2).*((D./E).^2);

  theta = np.linspace(-math.pi / 2, math.pi / 2, 1000)


  wl = 343.3 / f



  A = np.sin(math.pi * a * np.sin(theta)/wl)
  B = math.pi * a * np.sin(theta)/wl
  C = ((2 * math.pi * d * np.sin(theta)/wl) + delay * f)
  D = np.sin((N/2)*C)
  E = np.sin(C)
  I = ((A/B)**2 * (D/E)**2)


  return I

if __name__ == "__main__":
    fig, ax = plt.subplots()
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    fig3, ax3 = plt.subplots()
    fig4, ax4 = plt.subplots()
    fig5, ax5 = plt.subplots()
    fig6, ax6 = plt.subplots()


    for i in [100., 800., 3000., 10000]:
        ax.plot(theta * 180 / math.pi, amp_plot(i, .01, .01, 0), label = f'{i} Hz')
        ax.set_xlabel('Theta (Degrees)')
        ax.set_ylabel('Intensity')
        ax.legend()


    ax1.set_xlabel('Theta (Degrees)')
    ax1.set_ylabel('Decibels')
    ax1.plot(theta * 180 / math.pi, 10*np.log(amp_plot(i, .01, .01, 0)), label = f'{i} Hz')
    ax1.legend()

    ax2.set_xlabel('Theta (Degrees)')
    ax2.set_ylabel('Decibels')
    ax2.plot(theta * 180 / math.pi, 10*np.log(amp_plot(i, .01, .03, 0)), label = f'{i} Hz')
    ax2.legend()

    ax3.set_xlabel('Theta (Degrees)')
    ax3.set_ylabel('Decibels')
    ax3.plot(theta * 180 / math.pi, 10*np.log(amp_plot(i, .01, .05, 0)), label = f'{i} Hz')
    ax3.legend()

    ax4.set_xlabel('Theta (Degrees)')
    ax4.set_ylabel('Decibels')
    ax4.plot(theta * 180 / math.pi, 10*np.log(amp_plot(i, .03, .03, 0)), label = f'{i} Hz')
    ax4.legend()

    ax5.set_xlabel('Theta (Degrees)')
    ax5.set_ylabel('Decibels')
    ax5.plot(theta * 180 / math.pi, 10*np.log(amp_plot(i, .05, .03, 0)), label = f'{i} Hz')
    ax5.legend()

    ax6.set_xlabel('Theta (Degrees)')
    ax6.set_ylabel('Decibels')
    line, = ax6.plot(theta * 180 / math.pi, 10*np.log(amp_plot(i, .01, .05, .14e-3)), label = f'{i} Hz')
    ax6.legend()

    ax1.set_title("1 cm between speakers, Speakers are 1cm wide")
    ax2.set_title("1 cm between speakers, Speakers are 3cm wide")
    ax3.set_title("1 cm between speakers, Speakers are 5cm wide")
    ax4.set_title("3 cm between speakers, Speakers are 3cm wide")
    ax5.set_title("5 cm between speakers, Speakers are 3cm wide")
    ax6.set_title("1 cm between speakers, Speakers are 5cm wide, .5 ms delay")



    distances = np.linspace(.02, 0.1, 50)
    fig7, ax7 = plt.subplots()
    # scat = ax7.scatter(t[0], z[0], c="b", s=5, label=f'v0 = {v0} m/s')
    lines = []
    for i in [100., 800., 3000., 10000]:
        lines += ax7.plot(theta, 10*np.log(amp_plot(i, .01, .05, 0)), label = i)
        # ax7.set(xlim=[0, 3], ylim=[-4, 10], xlabel='Time [s]', ylabel='Z [m]')
        ax7.set_title('Animation')
        ax7.legend()

    def update(frame):
        ax7.clear()
        lines = []
        for x, i in enumerate([100, 400, 800, 1000, 1500, 2000, 2500, 3000, 10000]):
            # for each frame, update the data stored on each artist.
            # update the scatter plot:
            # data = np.stack([x, y]).T
            # scat.set_offsets(data)
            # update the line plot:
            ax7.set_ylabel('dB')
            ax7.set_xlabel('Theta (Degrees)')
            ax7.set_title(f'D={int(distances[frame] * 100)}cm, W = 3cm, N = 120')
            ax7.set_ylim(-100, 100)
            lines += ax7.plot(theta * 180 / math.pi, 10*np.log(amp_plot(i, distances[frame], .035, 0)), label = f'{i} Hz')
            ax7.legend(loc = 'lower right')
            # lines[x].set_xdata(theta)
            # lines[x].set_ydata(10*np.log(amp_plot(i, distances[frame], .01, 0)))
        return (line for line in lines)



    ani = animation.FuncAnimation(fig=fig7, func=update, frames=50, interval=100)
    ani

    # converting to an html5 video
    video = ani.to_html5_video()

    # embedding for the video
    html = display.HTML(video)

    # draw the animation
    display.display(html)
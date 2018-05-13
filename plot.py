import matplotlib.pyplot as plt
import numpy
t = numpy.linspace(0, 10, 40)
print("ttttttttt = %d",len(t))
print(t)
plt.plot(t, [1,2,3,4], 'ro')
#plt.axis([0, 6, 0, 20])
plt.show()

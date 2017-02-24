import pointer

ppdouble = pointer.PPDouble()
ppdouble.shape = 3

double1 = pointer.Double(1.)
double2 = pointer.Double(3.)

ppdouble.setpointer(0, double1)
ppdouble.setpointer(1, double2)

print ppdouble[0]
print ppdouble[1]
print ppdouble[2]

double1 += 1.
double2 *= 3.

print ppdouble[0]
print ppdouble[1]


#lst = []
#for i in xrange(10000000):
#    lst.append(pointer.PPDouble(1000000))
    #temp = pointer.PPDouble(1000000)

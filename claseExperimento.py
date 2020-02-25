import time
from funcionesBalanza import *

class subExp:
	def __init__(self, tempInicial, tempFinal, tiempoTotal, tiempoPaso, presionInicial, presionFinal, flujoInicial1, flujoInicial2, flujoInicial3, flujoFinal1, flujoFinal2, flujoFinal3):

		self.tiempoPaso = tiempoPaso
		self.tiempoTotal = tiempoTotal
		self.pasos = self.tiempoTotal/self.tiempoPaso

		self.tempInicial = tempInicial
		self.tempFinal = tempFinal
		self.tempPaso = (tempFinal - tempInicial)/self.pasos

		self.presionInicial = presionInicial
		self.presionFinal = presionFinal
		self.presionPaso = (presionFinal - presionInicial)/self.pasos

		self.flujoInicial1 	= flujoInicial1
		self.flujoInicial2 	= flujoInicial2
		self.flujoInicial3 	= flujoInicial3
		self.flujoFinal1	= flujoFinal1
		self.flujoFinal2	= flujoFinal2
		self.flujoFinal3	= flujoFinal3

		self.flujoPaso1	= (flujoFinal1 - flujoInicial1)/self.pasos
		self.flujoPaso2	= (flujoFinal2 - flujoInicial2)/self.pasos
		self.flujoPaso3	= (flujoFinal3 - flujoInicial3)/self.pasos

		self.flujo1 	= flujoInicial1
		self.flujo2 	= flujoInicial2
		self.flujo3 	= flujoInicial3
		self.temp = tempInicial
		self.presion = presionInicial
		self.tiempo = 0.0
 
	def actualizaSetPoints(self):

		self.tiempo += self.tiempoPaso

		self.temp 	+= self.tempPaso
		self.presion += self.presionPaso

		self.flujo1 += self.flujoPaso1
		self.flujo2 += self.flujoPaso2
		self.flujo3 += self.flujoPaso3

	def seteaVariables(self):

		#print(self.temp)
		seteaTemperaturaHorno(self.temp)
		#seteaTemperaturaBaño?
		#controlaPresion(self.presion)
		seteaCaudalMasico(self.flujo1, 1)
		seteaCaudalMasico(self.flujo1, 2)
		seteaCaudalMasico(self.flujo1, 3)

	def mideVariables(self):

		self.masa = 0. #mideBalanza()
		self.tempMedida= mideTemperaturaMuestra(30) #30 -> samplesOptimos(self.tiempoPaso)
		self.presionBaja = midePresionBaja(30) #30 -> samplesOptimos(self.tiempoPaso)
		self.presionAlta = midePresionAlta(30) #30 -> samplesOptimos(self.tiempoPaso)
		self.caudalMedido1 = mideCaudalMasico(30, 1) #30 -> samplesOptimos(self.tiempoPaso)
		self.caudalMedido2 = mideCaudalMasico(30, 2) #30 -> samplesOptimos(self.tiempoPaso)
		self.caudalMedido3 = mideCaudalMasico(30, 3) #30 -> samplesOptimos(self.tiempoPaso)

	def imprimeArchivo(self, tiempoExterno, f):

		f.write("{:.2f}".format(tiempoExterno + self.tiempo)+" ")
		f.write("{:.3f}".format(self.presion)+" ")
		f.write("{:.3f}".format(self.temp)+" ")
		f.write("{:.3f}".format(self.masa)+" ")
		f.write("{:.3f}".format(self.tempMedida)+" ")
		f.write("{:.3f}".format(self.presionBaja)+" ")
		f.write("{:.3f}".format(self.presionAlta)+" ")
		f.write("{:.3f}".format(self.caudalMedido1)+" ")
		f.write("{:.3f}".format(self.caudalMedido2)+" ")
		f.write("{:.3f}".format(self.caudalMedido3)+"\n")

	def condicion(self):

		#acá seteo, al inicializar, la condicion que me pinte
		#por ahora solo el tiempo
		if(self.tiempo<=self.tiempoTotal - self.tiempoPaso):
			return 0
		else:
			return 1






class Exp:
	expLista = []
	tiempo = 0.0

	def añadeSubExp(self, subExp):
		self.expLista.append(subExp)

	def ejecuta(self, filename, *args):

		with open(filename, "w") as f:

			f.write("t     p	      T	     m	   Tmedida Pbaja  Palta  Caudal1 Caudal2 Caudal3 \n")

			for subExp in self.expLista:

				while(subExp.condicion() == 0):

					subExp.seteaVariables()
					subExp.mideVariables()
					subExp.imprimeArchivo(self.tiempo, f)
					subExp.actualizaSetPoints()
					time.sleep(subExp.tiempoPaso)
					
				self.tiempo += subExp.tiempo


def prueba():

	archivo = "prueba.dat"

	subExperimento1 = subExp(25.0, 150.0, 10., 0.1, 760, 760, 0., 0., 0., 0., 100., 0.)
	subExperimento2 = subExp(150.0, 150.0, 10., 0.5, 760, 760, 0., 0., 0., 0., 100., 0.)
	subExperimento3 = subExp(150.0, 35.0, 10., 0.1, 760, 760, 0., 0., 0., 0., 100., 0.)
	subExperimento4 = subExp(35.0, 35.0, 10., 0.5, 760, 760, 0., 0., 0., 0., 100., 0.)

	primerExperimento = Exp()
	primerExperimento.añadeSubExp(subExperimento1)
	primerExperimento.añadeSubExp(subExperimento2)
	primerExperimento.añadeSubExp(subExperimento3)
	primerExperimento.añadeSubExp(subExperimento4)

	primerExperimento.ejecuta(archivo)

#prueba()





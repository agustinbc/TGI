from funcionesBalanza import *

import os
import shutil

from tkinter import *
from tkinter import ttk

from tkinter import messagebox
from tkinter import filedialog


#from scipy.optimize import curve_fit

import numpy as np
import matplotlib as mpl
import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.pyplot as plt
#plt.tight_layout()


#plt.style.use('ggplot')

import datetime

import time
import random
import queue
import threading

estoy_balanza = 0

class subExp:
	def __init__(self, 
				tempInicial, tempFinal, 
				tiempoTotal, tiempoPaso, 
				presionInicial, presionFinal, 
				flujoInicial1, flujoInicial2, flujoInicial3, 
				flujoFinal1, flujoFinal2, flujoFinal3, 
				queuePressure,
				checkboxFlujo1, checkboxFlujo2, checkboxFlujo3,
				checkboxFlujoHorno, checkboxFlujoVenteo, checkboxFlujoVenteoHorno,
				condicion_salida):
		self.queuePressure = queuePressure
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

		self.purga = 0
		self.setZero = 0

		self.checkboxFlujo1 = checkboxFlujo1
		self.checkboxFlujo2 = checkboxFlujo2
		self.checkboxFlujo3 = checkboxFlujo3
		self.checkboxFlujoHorno = checkboxFlujoHorno
		self.checkboxFlujoVenteo = checkboxFlujoVenteo
		self.checkboxFlujoVenteoHorno = checkboxFlujoVenteoHorno

		self.condicion_salida = condicion_salida

		self.auxiliarDerivadasM = []
		self.auxiliarDerivadasT = []
		self.auxiliarDerivadasP = []
		self.auxiliarDerivadast = []

		self.puntosDerivada = 5
		self.controlado = 0


		self.seteaValvulas()
 
	def actualizaSetPoints(self):

		self.tiempo += self.tiempoPaso

		self.temp 	+= self.tempPaso
		self.presion += self.presionPaso

		self.flujo1 += self.flujoPaso1
		self.flujo2 += self.flujoPaso2
		self.flujo3 += self.flujoPaso3

	def seteaVariables(self):
		epsilon = 0.05
		seteaTemperaturaHorno(self.temp)
		if self.presion > 760 and (self.flujo1+self.flujo2+self.flujo3) != 0:
			if self.tiempoControl():
				self.seteaPresion() #Esto está así porque me tengo que comunicar con el otro hilo y no con un instrumento.
				pass
		seteaCaudalMasico(self.flujo1, 1)
		seteaCaudalMasico(self.flujo2, 2)
		seteaCaudalMasico(self.flujo3, 3)

	def seteaPresion(self):
		vector_presion = [self.presion, self.presionAlta, self.mideDerivada("P"), self.flujo3+self.flujo2+self.flujo1]
		self.queuePressure.put(vector_presion)
		pass

	def mideVariables(self):

		if (estoy_balanza):
			self.masa = mideBalanza()
		else:
			self.masa = 0
		self.presionAlta = midePresionAlta(30)

		self.tempMedida= mideTemperaturaMuestra(30)
		
		self.presionBaja = midePresionBaja(30)

		self.caudalMedido1 = mideCaudalMasico(30, 1)
		self.caudalMedido2 = mideCaudalMasico(30, 2)
		self.caudalMedido3 = mideCaudalMasico(30, 3)

		self.auxiliarDerivadasP = self.auxiliarDerivadasP+[self.presionAlta]
		self.auxiliarDerivadasT = self.auxiliarDerivadasT+[self.tempMedida]
		self.auxiliarDerivadasM = self.auxiliarDerivadasM+[self.masa]

		self.auxiliarDerivadast = self.auxiliarDerivadast+[self.tiempo]

	def imprimeArchivo(self, tiempoExterno, file):
		file.write(str(tiempoExterno + self.tiempo)+" ")
		file.write(str(self.presion)+" ")
		file.write(str(self.temp)+" ")
		file.write(str(self.masa)+" ")
		file.write(str(self.tempMedida)+" ")
		file.write(str(self.presionBaja)+" ")
		file.write(str(self.presionAlta)+" ")
		file.write(str(self.flujo1)+" ")
		file.write(str(self.flujo2)+" ")
		file.write(str(self.flujo3)+" ")
		file.write(str(self.caudalMedido1)+" ")
		file.write(str(self.caudalMedido2)+" ")
		file.write(str(self.caudalMedido3)+"\n")

	def condicion(self):

		if (self.condicion_salida["t"][0] == 1):
			if(self.tiempo>=self.tiempoTotal):
				print('t')
				return 1

		if(self.condicion_salida["T"][0] == 1):
			if(abs(self.tempMedida-self.tempFinal)<self.condicion_salida["T"][1]): #1 es placeholder, eh
				print('T')
				return 1

		if(self.condicion_salida["p"][0] == 1):
			if(abs(self.presionAlta-self.presionFinal)<self.condicion_salida["p"][1]): #1 es placeholder, eh
				print('p')
				return 1

		if(self.condicion_salida["dT/dt"][0] == 1):
			if(abs(self.mideDerivada("T"))<self.condicion_salida["dT/dt"][1]):
				return 1

		if(self.condicion_salida["dm/dt"][0] == 1):
			if(abs(self.mideDerivada("M"))<self.condicion_salida["dm/dt"][1]):
				return 1

		if(self.condicion_salida["dp/dt"][0] == 1):
			if(abs(self.mideDerivada("P"))<self.condicion_salida["dp/dt"][1]):
				return 1

		return 0

	def mideDerivada(self, variable):

		arrayt = np.asarray(self.auxiliarDerivadast)
	

		if(len(self.auxiliarDerivadast) > self.puntosDerivada+1):

			if(variable == "T"):
				arrayT = np.asarray(self.auxiliarDerivadasT)
				coef = np.polyfit(arrayt[-1-self.puntosDerivada:], arrayT[-1-self.puntosDerivada:], 1)
				return round_sig(coef[0]/60.0, 4)

			if(variable == "P"):
				arrayP = np.asarray(self.auxiliarDerivadasP)
				coef = np.polyfit(arrayt[-1-self.puntosDerivada:], arrayP[-1-self.puntosDerivada:], 1)
				return round_sig(coef[0],4)

			if(variable == "M"):
				arrayM = np.asarray(self.auxiliarDerivadasM)
				#coef = np.polyfit(arrayt[-1-self.puntosDerivada:], arrayM[-1-self.puntosDerivada:], 1)
				return 10000

		return 10000

	def vectorVariables(self, tiempoExterno):

		dicc = {"masa":self.masa,
				"temp":self.tempMedida,
				"baja":self.presionBaja,
				"alta":self.presionAlta,
				"cau1":self.caudalMedido1,
				"cau2":self.caudalMedido2,
				"cau3":self.caudalMedido3,
				"tiem":self.tiempo+tiempoExterno,
				"tset":self.temp,
				"pset":self.presion,
				"1set":self.flujo1,
				"2set":self.flujo2,
				"3set":self.flujo3,
				"dpdt":self.mideDerivada("P"),
				"dTdt":self.mideDerivada("T"),
				"dmdt":self.mideDerivada("M")}

		return dicc

	def seteaValvulas(self):
		self.vectorValvulas = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		if(self.flujoInicial1 or self.flujoFinal1 or self.checkboxFlujo1):
			self.vectorValvulas[0] = self.vectorValvulas[3]  = 1

		if(self.flujoInicial2 or self.flujoFinal2 or self.checkboxFlujo2):
			self.vectorValvulas[1] = self.vectorValvulas[2]  = 1

		if(self.flujoInicial3 or self.flujoFinal3 or self.checkboxFlujo3):
			self.vectorValvulas[4] = self.vectorValvulas[5]  = 1

		if(self.checkboxFlujoHorno):
			self.vectorValvulas[15] = 1

		if(self.checkboxFlujoVenteoHorno):
			self.vectorValvulas[13] = self.vectorValvulas[14] = 1

		if(self.checkboxFlujoVenteo):
			self.vectorValvulas[7] = 1

		if(self.presionInicial > 760 or self.presionFinal > 760):
			self.vectorValvulas[9]  = 1

		#Todas las demás válvulas serán utilizadas bajo estricto comando del buen Facu/Pierre

	def overrideaValvulas(self, vectorExterno):

		self.vectorValvulas = vectorExterno.copy()

	def cambiaValvulas(self):

		vectorActual = mideVectorValvulas()
		print(vectorActual)
		print(self.vectorValvulas)

		for valvula in range(len(self.vectorValvulas)):
			if (self.vectorValvulas[valvula] != vectorActual[valvula]):
				if(self.vectorValvulas[valvula]==1):
					abreValvula(valvula)

				elif(self.vectorValvulas[valvula]==0):
					cierraValvula(valvula)

		#vectorActual = mideVectorValvulas()
		#print(vectorActual)

	def mideDerivadaInicial(self):

		arrayt = np.asarray(self.auxiliarDerivadast)
		arrayP = np.asarray(self.auxiliarDerivadasP)
		coef = np.polyfit(arrayt[0:self.puntosDerivada], arrayP[0:self.puntosDerivada], 1)
		return coef[0] 

	def tiempoControl(self):
		if self.tiempo%6 == 0 and self.tiempo != 0:
			print("Controla")
			return 1
		return 0

class Exp:
	def __init__(self, queue):
		self.expLista = []
		self.kill = 0
		self.tiempo = 0.0
		self.correExperimento = 0
		self.archivo = None
		self.queue = queue
		self.saltaSubExp = 0
		self.correExperimentoPresion = 0
		self.correExperimento = 0
		self.definePosicion = 0
		self.buscaPosicion = 0
		self.presionReducidaBuscada = 0
		self.actualizaPresionEquilibrioFlag = 0
		self.dndp = None
		self.subExpCorriendo = 0
		self.tiempoSubExp = 0

	def añadeSubExp(self, subExp):
		self.expLista.append(subExp)
		pass

	def ejecuta(self, *args):
		try:
			if self.kill:
				print("boom")
				return 0
			fname = self.archivo
			with open(fname, "w") as f:
				for subExp in self.expLista:
					subExp.cambiaValvulas()

					to = time.clock()

					while(subExp.condicion() == 0):

						if(self.saltaSubExp == 1 or self.kill):
							self.saltaSubExp = 0
							break

						t_init = time.clock()


						subExp.mideVariables()


						subExp.seteaVariables()


						subExp.imprimeArchivo(self.tiempo, f)

						subExp.actualizaSetPoints()

						self.queue.put(subExp.vectorVariables(self.tiempo))

						t_final = time.clock()
						try:
							time.sleep(subExp.tiempoPaso - t_final + t_init)
						except ValueError:
							print("no espere el tiempo")
						self.tiempoSubExp += subExp.tiempoPaso
						
					self.tiempo += subExp.tiempo
					self.subExpCorriendo += 1
					self.tiempoSubExp = 0
		except TypeError:
			messagebox.showinfo("Error", "Poné un nombre para el archivo")

		tf = time.clock()
		print(to, tf)

	def ejecutaPresion(self, *args):

		dicc = {"t": [1], 
			"T": [0,0], 
			"p": [0,0], 
			"dp/dt": [1, 0.05], # Diccionario de condiciones de salida.
			"dT/dt": [0,0],
			"dm/dt": [0,0]}

		queue_R = queue.Queue()
		
		fname = "CalibracionPresion.dat"

		with open(fname, "w") as f, open('presionesEquilibrio.dat', 'w') as fp:

			for caudal in [450]:

				direccion = 'subiendo'

				condicion_total = 0

				self.tiempo = 0
				pasos = 0


				while(condicion_total == 0):

					if(direccion == "subiendo"):				

						subExpAux = subExp( 0,0,
										72000.0,3.0,
										1000.0,1000.0, 
										0,0 , caudal, 
										0,0 , caudal, 
										queue_R,
										0,0,1 ,
										1,0,0 ,
										dicc)

						subExpAux.cambiaValvulas()

						while(subExpAux.condicion() == 0):

							if(self.saltaSubExp == 1):
								self.saltaSubExp = 0
								break

							t_init = time.clock()
							subExpAux.seteaVariables()
							subExpAux.mideVariables()
							subExpAux.imprimeArchivo(self.tiempo, f)
							subExpAux.actualizaSetPoints()
							self.queue.put(subExpAux.vectorVariables(self.tiempo))
							t_final = time.clock()
							time.sleep(subExpAux.tiempoPaso - t_final + t_init)
							
						self.tiempo += subExpAux.tiempo
						pasos += 1

						fp.write(str(pasos) + '\t' + str(self.tiempo) + '\t' + str(subExpAux.presion) + str(subExpAux.ajustaLaExponencial) +'\n')

						if(abs(subExpAux.mideDerivadaInicial()) >= 0.05):

							abreValvula("PCC")
							tiempo_inicial = time.clock()
							time.sleep(2.0)
							tiempo_final = time.clock()
							cierraValvula("PCC")
							print(tiempo_final - tiempo_inicial)
						if(abs(subExpAux.mideDerivadaInicial()) < 0.05):
							condicion_total += 1
							direccion = "bajando"

					if(direccion == "bajando"):				

						subExpAux = subExp( 0,0,
										72000.0,3.0,
										1000.0,1000.0, 
										0,0 , caudal, 
										0,0 , caudal, 
										queue_R,
										0,0,1 ,
										1,0,0 ,
										dicc)

						subExpAux.cambiaValvulas()

						while(subExpAux.condicion() == 0):

							if(self.saltaSubExp == 1):
								self.saltaSubExp = 0
								break

							t_init = time.clock()
							subExpAux.seteaVariables()
							subExpAux.mideVariables()
							subExpAux.imprimeArchivo(self.tiempo, f)
							subExpAux.actualizaSetPoints()
							self.queue.put(subExpAux.vectorVariables(self.tiempo))
							t_final = time.clock()
							time.sleep(subExpAux.tiempoPaso - t_final + t_init)
							
						self.tiempo += subExpAux.tiempo
						pasos += 1
						fp.write(str(pasos) + '\t' + str(self.tiempo) + '\t' + str(subExpAux.presion) + str(subExpAux.ajustaLaExponencial) +'\n')

						if(abs(subExpAux.mideDerivadaInicial()) >= 0.05 ):
							abreValvula("PCO")

							tiempo_inicial = time.clock()
							time.sleep(2.0)
							tiempo_final = time.clock()
							
							cierraValvula("PCO")
							pasos += 1
						if(abs(subExpAux.mideDerivadaInicial()) < 0.05):
							condicion_total += 1
							direccion = "subiendo"

	def ejecutaInicializador(self, *args):
		dicc = {"t": [1], 
			"T": [0,0], 
			"p": [0,0], 
			"dp/dt": [0,0], # Diccionario de condiciones de salida.
			"dT/dt": [0,0],
			"dm/dt": [0,0]}

		queue_R = queue.Queue()

		subExpAux = subExp( 0,0,
						72000.0,3.0,
						1000.0,1000.0, 
						0,0 , 50.0, 
						0,0 , 50.0, 
						queue_R,
						0,0,1 ,
						1,0,0 ,
						dicc)

		subExpAux.cambiaValvulas()

		while(subExpAux.condicion() == 0):

			if(self.saltaSubExp == 1):
				self.saltaSubExp = 0
				break

			t_init = time.clock()
			subExpAux.seteaVariables()
			subExpAux.mideVariables()
			subExpAux.imprimeArchivo(self.tiempo, f)
			subExpAux.actualizaSetPoints()
			self.queue.put(subExpAux.vectorVariables(self.tiempo))
			t_final = time.clock()
			time.sleep(subExpAux.tiempoPaso - t_final + t_init)
			
		self.tiempo += subExpAux.tiempo
		pasos += 1

		print(subExpAux.ajustaLaExponencial)

	def definedNdp(self, *args):

		self.definePosicion = 0
		
		with open('auxiliarTau.dat', 'w') as f:
			dicc = {"t": [1], 
				"T": [0,0], 
				"p": [0, 0], 
				"dp/dt": [0, 0], # Diccionario de condiciones de salida.
				"dT/dt": [0,0],
				"dm/dt": [0,0]}
	
			queue_R = queue.Queue()
	
			self.presionAtmosferica = 740
			self.presionesEquilibrioPosicion1 = None
			self.presionesEquilibrioPosicion2 = None
	
			subExpAux = subExp( 0,0,
							60.0, 2.0,
							750.0,2000.0, 
							0,0 , 300.0, 
							0,0 , 300.0, 
							queue_R,
							0,0,1 ,
							1,0,0 ,
							dicc)
	
			subExpAux.cambiaValvulas()
			subExpAux.mideVariables()
	
			while(subExpAux.condicion() == 0):
	
				if(subExpAux.mideDerivada("P")<0.01):
					self.presionesEquilibrioPosicion1 = midePresionAlta(30)
					break
	
				if(self.saltaSubExp == 1):
					self.saltaSubExp = 0
					break
	
				t_init = time.clock()
				subExpAux.seteaVariables()
				subExpAux.mideVariables()
				subExpAux.imprimeArchivo(self.tiempo, f)
				subExpAux.actualizaSetPoints()
				self.queue.put(subExpAux.vectorVariables(self.tiempo))
				t_final = time.clock()
				time.sleep(subExpAux.tiempoPaso - t_final + t_init)
	
			if(self.presionesEquilibrioPosicion1 == None):	
				self.tiempo += subExpAux.tiempo
				self.tiempoInicioBajada = self.tiempo
		
				subExpAux = subExp( 0,0,
								60.0, 2.0,
								1000.0,0.0, 
								0,0 , 0.0, 
								0,0 , 0.0, 
								queue_R,
								0,0,1 ,
								1,0,0 ,
								dicc)
	
				subExpAux.mideVariables()
		
				while(subExpAux.condicion() == 0 and self.presionesEquilibrioPosicion1 == None):
			
					if(self.saltaSubExp == 1):
						self.saltaSubExp = 0
						break
		
					t_init = time.clock()
					subExpAux.seteaVariables()
					subExpAux.mideVariables()
					subExpAux.imprimeArchivo(self.tiempo, f)
					subExpAux.actualizaSetPoints()
					self.queue.put(subExpAux.vectorVariables(self.tiempo))
					t_final = time.clock()
					time.sleep(subExpAux.tiempoPaso - t_final + t_init)

				arrayt = np.asarray(subExpAux.auxiliarDerivadast)

				arrayP = np.asarray(subExpAux.auxiliarDerivadasP)
			
				coef = np.polyfit(arrayt[2:subExpAux.puntosDerivada+2], arrayP[2:subExpAux.puntosDerivada+2], 1)
			
				self.Tau = (self.presionAtmosferica - coef[1])/coef[0] - 2 * subExpAux.tiempoPaso#acá hallo tau, con tau la presion
	
				self.presionesEquilibrioPosicion1 = convierteTauPresion(self.Tau, 300.0)


			abreValvula("PCO")
			time.sleep(1.0)
			cierraValvula("PCO")

			subExpAux = subExp( 0,0,
							60.0, 2.0,
							750.0,2000.0, 
							0,0 , 300.0, 
							0,0 , 300.0, 
							queue_R,
							0,0,1 ,
							1,0,0 ,
							dicc)
	
			subExpAux.cambiaValvulas()
			subExpAux.mideVariables()
	
			while(subExpAux.condicion() == 0):
	
				if(subExpAux.mideDerivada("P")<0.01):
					self.presionesEquilibrioPosicion2 = midePresionAlta(30)
					break
	
				if(self.saltaSubExp == 1):
					self.saltaSubExp = 0
					break
	
				t_init = time.clock()
				subExpAux.seteaVariables()
				subExpAux.mideVariables()
				subExpAux.imprimeArchivo(self.tiempo, f)
				subExpAux.actualizaSetPoints()
				self.queue.put(subExpAux.vectorVariables(self.tiempo))
				t_final = time.clock()
				time.sleep(subExpAux.tiempoPaso - t_final + t_init)
	
			if(self.presionesEquilibrioPosicion2 == None):	
				self.tiempo += subExpAux.tiempo
				self.tiempoInicioBajada = self.tiempo
		
				subExpAux = subExp( 0,0,
								60.0, 2.0,
								1000.0,0.0, 
								0,0 , 0.0, 
								0,0 , 0.0, 
								queue_R,
								0,0,1 ,
								1,0,0 ,
								dicc)
	
				subExpAux.mideVariables()
		
				while(subExpAux.condicion() == 0 and self.presionesEquilibrioPosicion2 == None):
			
					if(self.saltaSubExp == 1):
						self.saltaSubExp = 0
						break
		
					t_init = time.clock()
					subExpAux.seteaVariables()
					subExpAux.mideVariables()
					subExpAux.imprimeArchivo(self.tiempo, f)
					subExpAux.actualizaSetPoints()
					self.queue.put(subExpAux.vectorVariables(self.tiempo))
					t_final = time.clock()
					time.sleep(subExpAux.tiempoPaso - t_final + t_init)

				arrayt = np.asarray(subExpAux.auxiliarDerivadast)

				arrayP = np.asarray(subExpAux.auxiliarDerivadasP)
			
				coef = np.polyfit(arrayt[2:subExpAux.puntosDerivada+2], arrayP[2:subExpAux.puntosDerivada+2], 1)
			
				self.Tau = (self.presionAtmosferica - coef[1])/coef[0] - 2 * subExpAux.tiempoPaso#acá hallo tau, con tau la presion
	
				self.presionesEquilibrioPosicion2 = convierteTauPresion(self.Tau, 300.0)


			self.presionReducidaEquilibrio = self.presionesEquilibrioPosicion2*(50/300)**0.937
			

			self.dndp = (self.presionesEquilibrioPosicion2 - self.presionesEquilibrioPosicion1) * (300/50)**0.937

			print(self.dndp, self.presionesEquilibrioPosicion1, self.presionesEquilibrioPosicion2)

	def buscaPosicionValvula(self, *args):

		self.buscaPosicion = 0

		if(self.presionReducidaBuscada < self.presionReducidaEquilibrio):
			abreValvula("PCO")
			dn = self.dndp*(self.presionReducidaEquilibrio - self.presionReducidaBuscada)
			time.sleep(dn)
			cierraValvula("PCO")
		else:
			abreValvula("PCC")
			dn = self.dndp*(self.presionReducidaBuscada - self.presionReducidaEquilibrio)
			time.sleep(dn)
			cierraValvula("PCC")

		self.presionReducidaAnterior = self.presionReducidaEquilibrio
		self.presionReducidaEquilibrio = self.presionReducidaBuscada
		self.ultimaApertura = dn
		print(dn)

	def actualizaPresionEquilibrio(self, presion, flujo, *args):

		self.actualizaPresionEquilibrioFlag = 0

		presionReducida = presion*(flujo/50)**0.937	

		self.presionReducidaAnterior = self.presionReducidaEquilibrio
		self.presionReducidaEquilibrio = presionReducida

		self.actualizadNdp()

	def actualizadNdp(self, *args):

		self.dndp = (self.presionReducidaEquilibrio - self.presionReducidaAnterior)/self.ultimaApertura

class GUI:
	def __init__(self, root, queue, queuePressure, kill):
		
		self.experimentos = 0

		self.experimentoVariable = Exp(queue)

		self.queue = queue
		self.queuePressure = queuePressure
		self.root = root

		self.root.state('zoomed')

		self.nb = ttk.Notebook(self.root)


		self.nb.grid(row=0, column = 0)
		
		self.logs =ttk.Frame(self.nb)
		self.med = ttk.Frame(self.nb)
		self.exp = ttk.Frame(self.nb)
		self.grp = ttk.Frame(self.nb)
	
		self.root.title("Termobalanza - ver 1.0")
	
	

		self.nb.add(self.exp, text = "Experimento")
		self.nb.add(self.logs,text = "Historial")
		self.nb.add(self.grp, text = "Gráficos")
		self.nb.add(self.med, text = "Mediciones")


		self.inicializaVariables()

		self.armaVentanaExperimentos()
		self.armaVentanaMediciones()
		self.armaVentanaGraficos()
		self.armaVentanaLogs(kill)

		for child in self.framePanel.winfo_children(): child.grid_configure(padx=5, pady=0)
		for child in self.frameExperimentos.winfo_children(): child.grid_configure(padx=2, pady=5)
		for child in self.frameGraficos.winfo_children(): child.grid_configure(padx = 2, pady = 5)
		for child in self.frameLogs.winfo_children(): child.grid_configure(padx = 2, pady = 5)

	def armaVentanaMediciones(self):


		self.framePanel = ttk.Frame(self.med, padding="10 10 12 12")
		self.framePanel.grid(column=0, row=0, sticky=(N, W, E, S))

		# Medición de valores de entradas analógicas

		ttk.Label(self.framePanel, text="Presión baja").grid(column=1, row=5, sticky=(W, E))
		ttk.Label(self.framePanel, text="Presión alta").grid(column=1, row=6, sticky=(W, E))
		ttk.Label(self.framePanel, text="Temperatura muestra").grid(column=1, row=7, sticky=(W, E))

		ttk.Button(self.framePanel, text="Medir", command = self.actualizaValores).grid(column=3, row=6, sticky=W)

		ttk.Label(self.framePanel, textvariable=self.presionBaja).grid(column=2, row=5, sticky=(W, E))
		ttk.Label(self.framePanel, textvariable=self.presionAlta).grid(column=2, row=6, sticky=(W, E))
		ttk.Label(self.framePanel, textvariable=self.tempMuestra).grid(column=2, row=7, sticky=(W, E))

		ttk.Entry(self.framePanel, width=7, textvariable = self.tempHorno).grid(column=2, row = 11, sticky =(W,E))
		ttk.Entry(self.framePanel, width=7, textvariable = self.tempBaño).grid(column=2, row = 12, sticky =(W,E))

		# Seteo de valores salidas analógicas

		ttk.Label(self.framePanel, text="Temperatura horno").grid(column=1, row=11, sticky=(W, E))
		ttk.Label(self.framePanel, text="Temperatura baño").grid(column=1, row=12, sticky=(W, E))

		ttk.Button(self.framePanel, text="Setear", command=self.botonTemperaturaHorno).grid(column=3, row=11, sticky=W)
		ttk.Button(self.framePanel, text="Setear", command=self.botonTemperaturaBaño).grid(column=3, row=12, sticky=W)

		ttk.Label(self.framePanel, text="Caudal 1").grid(column=1, row=8, sticky=(W, E))
		ttk.Label(self.framePanel, text="Caudal 2").grid(column=1, row=9, sticky=(W, E))
		ttk.Label(self.framePanel, text="Caudal 3").grid(column=1, row=10, sticky=(W, E))

		ttk.Label(self.framePanel, textvariable=self.caudalMasa1).grid(column=2, row=8, sticky=(W, E))
		ttk.Label(self.framePanel, textvariable=self.caudalMasa2).grid(column=2, row=9, sticky=(W, E))
		ttk.Label(self.framePanel, textvariable=self.caudalMasa3).grid(column=2, row=10, sticky=(W, E))

		ttk.Entry(self.framePanel, width=7, textvariable = self.outMasa1).grid(column=2, row = 13, sticky =(W,E))
		ttk.Entry(self.framePanel, width=7, textvariable = self.outMasa2).grid(column=2, row = 14, sticky =(W,E))
		ttk.Entry(self.framePanel, width=7, textvariable = self.outMasa3).grid(column=2, row = 15, sticky =(W,E))

		ttk.Label(self.framePanel, text="Control Masa1").grid(column=1, row=13, sticky=(W, E))
		ttk.Label(self.framePanel, text="Control Masa2").grid(column=1, row=14, sticky=(W, E))
		ttk.Label(self.framePanel, text="Control Masa3").grid(column=1, row=15, sticky=(W, E))

		ttk.Button(self.framePanel, text="Setear", command=self.botonMFC1).grid(column=3, row=13, sticky=W)
		ttk.Button(self.framePanel, text="Setear", command=self.botonMFC2).grid(column=3, row=14, sticky=W)
		ttk.Button(self.framePanel, text="Setear", command=self.botonMFC3).grid(column=3, row=15, sticky=W)

		ttk.Button(self.framePanel, text="Medir", command=self.actualizaValoresMasa).grid(column=3, row=9, padx=10,sticky=W)

		ttk.Label(self.framePanel, text="Masa").grid(column=1, row=2, sticky=(W, E))

		ttk.Label(self.framePanel, textvariable=self.masa).grid(column=2, row=2, sticky=(W, E))

		ttk.Button(self.framePanel, text="Medir", command=self.botonMasa).grid(column=3, row=2, sticky=W)

		ttk.Label(self.framePanel, text="Set zero").grid(column=1, row=1, sticky=(W, E))

		ttk.Button(self.framePanel, text="Setear", command=seteaElZero).grid(column=2, row=1, sticky=W)


		# Manejo manual de la válvula

		ttk.Button(self.framePanel, text="Abrir PC", command=	self.boton10).grid(column = 1, row = 17)
		ttk.Button(self.framePanel, text="Cerrar PC", command=	self.boton01).grid(column = 1, row = 18)

		ttk.Button(self.framePanel, text="Abrir PC (t)", command=	lambda: self.abrirPC(self.tiempoPC.get())).grid(column = 2, row = 17)
		ttk.Button(self.framePanel, text="Cerrar PC (t)", command=	lambda: self.cerrarPC(self.tiempoPC.get())).grid(column = 2, row = 18)


		ttk.Label(self.framePanel, text="Tiempo PC").grid(column=1, row=19, sticky=(W, E))

		ttk.Entry(self.framePanel, width=7, textvariable = self.tiempoPC).grid(column=2, row = 19, sticky =(W,E))


		# Control de presión 2: PD

		ttk.Label(self.framePanel, text="-----------------Parametros Control PID-------------------").grid(column=3, row=20, rowspan = 3, columnspan = 15, sticky=(W, E))

		ttk.Label(self.framePanel, text="Constante P").grid(column=3, row=24, sticky=(W, E))
		ttk.Entry(self.framePanel, width=7, textvariable = self.alphaVar).grid(column=4, row = 24, sticky =(W,E))

		ttk.Label(self.framePanel, text="Constante I").grid(column=3, row=25, sticky=(W, E))
		ttk.Entry(self.framePanel, width=7, textvariable = self.gammaVar).grid(column=4, row = 25, sticky =(W,E))

		ttk.Label(self.framePanel, text="Constante D").grid(column=3, row=26, sticky=(W, E))
		ttk.Entry(self.framePanel, width=7, textvariable = self.betaVar).grid(column=4, row = 26, sticky =(W,E))

		ttk.Label(self.framePanel, text="Maximo tiempo").grid(column=5, row=24, sticky=(W, E))
		ttk.Entry(self.framePanel, width=7, textvariable = self.tmaxVar).grid(column=6, row = 24, sticky =(W,E))

		ttk.Label(self.framePanel, text="Maxima pendiente").grid(column=5, row=25, sticky=(W, E))
		ttk.Entry(self.framePanel, width=7, textvariable = self.dpmaxVar).grid(column=6, row = 25, sticky =(W,E))

		ttk.Label(self.framePanel, text="Maxima pendiente").grid(column=5, row=26, sticky=(W, E))
		ttk.Entry(self.framePanel, width=7, textvariable = self.deltaApMinVar).grid(column=6, row = 26, sticky =(W,E))


		ttk.Checkbutton(self.framePanel, text="Controlo?", variable = self.controlo).grid(column=2, row=25, sticky=W)






		#Calibración de la presión



		ttk.Label(self.framePanel, text="Valvula 1").grid(column=4, row=1, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 2").grid(column=4, row=2, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 3").grid(column=4, row=3, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 4").grid(column=4, row=4, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 5").grid(column=4, row=5, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 6").grid(column=4, row=6, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 7").grid(column=4, row=7, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 8").grid(column=4, row=8, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 9").grid(column=4, row=9, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 10").grid(column=4, row=10, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 11").grid(column=4, row=11, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 12").grid(column=4, row=12, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 13").grid(column=4, row=13, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 14").grid(column=4, row=14, sticky=(W, E))
		ttk.Label(self.framePanel, text="Valvula 15").grid(column=4, row=15, sticky=(W, E))

		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(1)).grid(column=5, row=1, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(2)).grid(column=5, row=2, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(3)).grid(column=5, row=3, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(4)).grid(column=5, row=4, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(5)).grid(column=5, row=5, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(6)).grid(column=5, row=6, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(7)).grid(column=5, row=7, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(8)).grid(column=5, row=8, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(9)).grid(column=5, row=9, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(10)).grid(column=5, row=10, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(11)).grid(column=5, row=11, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(12)).grid(column=5, row=12, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(13)).grid(column=5, row=13, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(14)).grid(column=5, row=14, sticky=W)
		ttk.Button(self.framePanel, text="Abrir", command=lambda: abreValvula(15)).grid(column=5, row=15, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(1)).grid(column=6, row=1, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(2)).grid(column=6, row=2, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(3)).grid(column=6, row=3, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(4)).grid(column=6, row=4, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(5)).grid(column=6, row=5, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(6)).grid(column=6, row=6, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(7)).grid(column=6, row=7, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(8)).grid(column=6, row=8, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(9)).grid(column=6, row=9, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(10)).grid(column=6, row=10, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(11)).grid(column=6, row=11, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(12)).grid(column=6, row=12, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(13)).grid(column=6, row=13, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(14)).grid(column=6, row=14, sticky=W)
		ttk.Button(self.framePanel, text="Cerrar", command=lambda: cierraValvula(15)).grid(column=6, row=15, sticky=W)

	def armaVentanaExperimentos(self):

		self.frameExperimentos = ttk.Frame(self.exp, padding="5 5 5 5")
		self.frameExperimentos.grid(column=0, row=0, sticky=(N, W, E, S))
		
	
		
		ttk.Label(self.frameExperimentos, text="Temp  ").grid(column=	1, row=1, sticky=(W, E))
		ttk.Label(self.frameExperimentos, text="Presion ").grid(column=		1, row=2, sticky=(W, E))
		ttk.Label(self.frameExperimentos, text="Gas 1 ").grid(column=		1, row=3, sticky=(W, E))
		ttk.Label(self.frameExperimentos, text="Gas 2 ").grid(column=		1, row=4, sticky=(W, E))
		ttk.Label(self.frameExperimentos, text="Gas 3 ").grid(column=		1, row=5, sticky=(W, E))
		ttk.Label(self.frameExperimentos, text="Tiempo t/dt").grid(column=			1, row=6, sticky=(W, E))
		#ttk.Label(self.frameExperimentos, text="Archivo").grid(column=		1, row=0, sticky=(W, E))

		ttk.Label(self.frameExperimentos, text="Descripción").grid(column=		1, row=7, sticky=(W, E))
		ttk.Label(self.frameExperimentos, text="Archivo").grid(column=		1, row=8, sticky=(W, E))
		ttk.Label(self.frameExperimentos, text="Carpeta").grid(column=		1, row=9,  sticky=(W, E))
		
		#ttk.Entry(self.frameExperimentos, width=7, textvariable =self.nombreArchivo).grid(column=	2, row = 0, columnspan=2, sticky =(W,E))
		self.entryTempInicial = ttk.Entry(self.frameExperimentos, width=7, textvariable = self.tempInicial)
		self.entryTempFinal = ttk.Entry(self.frameExperimentos, width=7, textvariable = self.tempFinal)
		self.entryPresInicial = ttk.Entry(self.frameExperimentos, width=7, textvariable = self.presionInicial)
		self.entryPresFinal = ttk.Entry(self.frameExperimentos, width=7, textvariable = self.presionFinal)

		self.entryTempInicial.grid(column=	2, row = 1, sticky =(W,E))
		self.entryTempFinal.grid(column=	3, row = 1, sticky =(W,E))
		self.entryPresInicial.grid(column=	2, row = 2, sticky =(W,E))
		self.entryPresFinal.grid(column=	3, row = 2, sticky =(W,E))

		self.entryTempInicial.config(state = DISABLED)
		self.entryTempFinal.config(state = DISABLED)
		self.entryPresInicial.config(state = DISABLED)
		self.entryPresFinal.config(state = DISABLED)



		self.flujoInicial1Entry = ttk.Entry(self.frameExperimentos, width=7, textvariable = self.flujo3Inicial)
		self.flujoInicial2Entry = ttk.Entry(self.frameExperimentos, width=7, textvariable = self.flujo2Inicial)
		self.flujoInicial3Entry = ttk.Entry(self.frameExperimentos, width=7, textvariable = self.flujo1Inicial)
		self.flujoInicial1Entry.grid(column=	2, row = 3, sticky =(W,E))
		self.flujoInicial2Entry.grid(column=	2, row = 4, sticky =(W,E))
		self.flujoInicial3Entry.grid(column=	2, row = 5, sticky =(W,E))

		self.flujoInicial1Entry.config(state = DISABLED)
		self.flujoInicial2Entry.config(state = DISABLED)
		self.flujoInicial3Entry.config(state = DISABLED)

		self.flujoFinal1Entry  = ttk.Entry(self.frameExperimentos, width=7, textvariable = self.flujo3Final)
		self.flujoFinal2Entry  = ttk.Entry(self.frameExperimentos, width=7, textvariable = self.flujo2Final)
		self.flujoFinal3Entry  = ttk.Entry(self.frameExperimentos, width=7, textvariable = self.flujo1Final)
		self.flujoFinal1Entry.grid(column=	3, row = 3, sticky =(W,E))
		self.flujoFinal2Entry.grid(column=	3, row = 4, sticky =(W,E))
		self.flujoFinal3Entry.grid(column=	3, row = 5, sticky =(W,E))

		self.flujoFinal1Entry.config(state = DISABLED)
		self.flujoFinal2Entry.config(state = DISABLED)
		self.flujoFinal3Entry.config(state = DISABLED)

		ttk.Label(self.frameExperimentos, text = "Masa inicial").grid(column = 1, row = 0, sticky=(W,E))
		ttk.Entry(self.frameExperimentos, textvariable = self.masaFicticia, width = 7).grid(column = 2, row = 0)
		ttk.Button(self.frameExperimentos, text = "SZ", command = lambda: seteaElZero(self.masaFicticia.get()), width = 7).grid(column = 3, row = 0)


		ttk.Entry(self.frameExperimentos, width=7, textvariable = self.tiempoTotal).grid(column=	2, row = 6, sticky =(W,E))
		ttk.Entry(self.frameExperimentos, width=7, textvariable = self.tiempoPaso).grid(column=	3, row = 6, sticky =(W,E))
		ttk.Button(self.frameExperimentos, width=18, text="Abrir...", command=		self.botonSeleccionarCarpeta).grid(	column=2, row=9,columnspan=2, sticky=W)
		ttk.Entry(self.frameExperimentos, width=7, textvariable =self.descripcion).grid(column=	2, row = 7, columnspan=2, sticky =(W,E))
		ttk.Entry(self.frameExperimentos, width=7, textvariable =self.nombreArchivo).grid(column=	2, row = 8, columnspan=2, sticky =(W,E))
		
		ttk.Button(self.frameExperimentos, text="Añadir", command=		self.añadeSubExp).grid(		column=1, row=13, sticky=W)
		ttk.Button(self.frameExperimentos, text="Modificar", command=	self.modificaSubExp).grid(	column=1, row=14, sticky=W)
		ttk.Button(self.frameExperimentos, text="Quitar", command=		self.remueveSubExp).grid(	column=1, row=15, sticky=W)
		ttk.Button(self.frameExperimentos, text="Saltar", command=		self.saltaSubExp).grid(		column=1, row=16, sticky=W)
		ttk.Button(self.frameExperimentos, text="Guardar", command=		self.botonGuardar).grid(	column=1, row=17, sticky=W)
		ttk.Button(self.frameExperimentos, text="Cargar", command=		self.botonCargar).grid(		column=1, row=18, sticky=W)
		ttk.Button(self.frameExperimentos, text="EJECUTAR!", command=	self.ejecutaExp).grid(		column=1, row=19, sticky=W)

		self.arbolExperimentos = ttk.Treeview(self.frameExperimentos, height=9, columns = ("Ti", "Tf","pi","pf","F1i","F2i","F3i","F1f","F2f","F3f", "t", "dt"))
		self.arbolExperimentos.grid(column=2, row=13, rowspan = 6, columnspan = 12, sticky = (E))
		
		self.arbolExperimentos.heading("#0", text = "N°")
		self.arbolExperimentos.column("#0", minwidth=0, width=40)
		self.arbolExperimentos.heading("Ti", text = "Ti[°C]")
		self.arbolExperimentos.column("Ti", minwidth=0, width=75)
		self.arbolExperimentos.heading("Tf", text = "Tf[°C]")
		self.arbolExperimentos.column("Tf", minwidth=0, width=75)
		self.arbolExperimentos.heading("F1i", text = "F1i[ccs]")
		self.arbolExperimentos.column("F1i", minwidth=0, width=75)
		self.arbolExperimentos.heading("F2i", text = "F2i[ccs]")
		self.arbolExperimentos.column("F2i", minwidth=0, width=75)
		self.arbolExperimentos.heading("F3i", text = "F3i[ccs]")
		self.arbolExperimentos.column("F3i", minwidth=0, width=75)
		self.arbolExperimentos.heading("F1f", text = "F1f[ccs]")
		self.arbolExperimentos.column("F1f", minwidth=0, width=75)
		self.arbolExperimentos.heading("F2f", text = "F2f[ccs]")
		self.arbolExperimentos.column("F2f", minwidth=0, width=75)
		self.arbolExperimentos.heading("F3f", text = "F3f[ccs]")
		self.arbolExperimentos.column("F3f", minwidth=0, width=75)
		self.arbolExperimentos.heading("pi", text = "pi[torr]")
		self.arbolExperimentos.column("pi", minwidth=0, width=70)	
		self.arbolExperimentos.heading("pf", text = "pf[torr]")
		self.arbolExperimentos.column("pf", minwidth=0, width=70)
		self.arbolExperimentos.heading("t", text = "t[s]")
		self.arbolExperimentos.column("t", minwidth=0, width=70)	
		self.arbolExperimentos.heading("dt", text = "dt[s]")
		self.arbolExperimentos.column("dt", minwidth=0, width=70)

		self.arbolExperimentos.bind("<Double-1>", self.obtengoValoresArbol)

		self.nbExp = ttk.Notebook(self.frameExperimentos)

		self.nbExp.grid(row=0, column = 5, rowspan=10, columnspan=12)
		
		self.graphTvst = ttk.Frame(self.nbExp)
		self.graphPvst = ttk.Frame(self.nbExp)
		self.graphFvst = ttk.Frame(self.nbExp)
		self.graphCustom = ttk.Frame(self.nbExp)
	
		self.root.title("Termobalanza - ver 0.1")
	
	
		self.nbExp.add(self.graphTvst, text = "Temperatura y tiempo")
		self.nbExp.add(self.graphPvst, text = "Presión y tiempo")
		self.nbExp.add(self.graphFvst, text = "Flujos y tiempo")
		self.nbExp.add(self.graphCustom, text = "Custom")


		self.canvasTvst = Canvas(self.graphTvst, width=750, height=300)
		self.canvasPvst = Canvas(self.graphPvst, width=750, height=300)
		self.canvasFvst = Canvas(self.graphFvst, width=750, height=300)
		self.canvasCustom = Canvas(self.graphCustom, width=750, height=300)

		self.canvasTvst.grid(row=0, column=0, columnspan = 15, rowspan =8)
		self.canvasPvst.grid(row=0, column=0, columnspan = 15, rowspan =8)
		self.canvasFvst.grid(row=0, column=0, columnspan = 15, rowspan =8)
		self.canvasCustom.grid(row=0, column=0, columnspan = 15, rowspan =8)



		self.progressBar = ttk.Progressbar(self.frameExperimentos, orient="horizontal", length=900, mode="determinate")
		self.progressBar.grid(row = 19, column = 2, columnspan = 15)

		ttk.Checkbutton(self.frameExperimentos , variable = self.checkboxTemperatura, command = self.botonCheckboxTemperatura).grid(row = 1, column = 4)
		ttk.Checkbutton(self.frameExperimentos , variable = self.checkboxPresion, command = self.botonCheckboxPresion).grid(row = 2, column = 4)
		ttk.Checkbutton(self.frameExperimentos , variable = self.checkboxFlujo1, command = self.botonCheckboxFlujo1).grid(row = 3, column = 4)
		ttk.Checkbutton(self.frameExperimentos , variable = self.checkboxFlujo2, command = self.botonCheckboxFlujo2).grid(row = 4, column = 4)
		ttk.Checkbutton(self.frameExperimentos , variable = self.checkboxFlujo3, command = self.botonCheckboxFlujo3).grid(row = 5, column = 4)

		ttk.Checkbutton(self.frameExperimentos, text = "G-H", variable = self.checkboxFlujoHorno).grid(row = 10, column = 1)

		ttk.Checkbutton(self.frameExperimentos, text = "G-V", variable = self.checkboxFlujoVenteo).grid(row = 10, column = 2)
		
		ttk.Checkbutton(self.frameExperimentos, text = "H-V", variable = self.checkboxFlujoVenteoHorno).grid(row = 10, column = 3)

		ttk.Label(self.frameExperimentos, text="-------Condiciones de salida--------").grid(row = 10, column= 4, columnspan = 10)

		ttk.Checkbutton(self.frameExperimentos , text = "t=tf", variable = self.checkboxCondiciont, command = self.botonCheckboxCondiciont).grid(row = 12, column = 1, sticky =E)

		ttk.Checkbutton(self.frameExperimentos , text = "|T-Tf|=", variable = self.checkboxCondicionT, command = self.botonCheckboxCondicionT).grid(row = 12, column = 3, sticky =E)
		self.entryTempSalida =ttk.Entry(self.frameExperimentos, width=5, textvariable = self.tempSalida)
		self.entryTempSalida.grid(column=	4, row = 12, sticky =(W,E))	
		self.entryTempSalida.config(state = DISABLED)

		ttk.Checkbutton(self.frameExperimentos , text = "|P-Pf|=", variable = self.checkboxCondicionP, command = self.botonCheckboxCondicionP).grid(row = 12, column = 5, sticky =E)
		self.entryPresSalida =ttk.Entry(self.frameExperimentos, width=5, textvariable = self.presSalida)
		self.entryPresSalida.grid(column=	6, row = 12, sticky =(W,E))
		self.entryPresSalida.config(state = DISABLED)


		ttk.Checkbutton(self.frameExperimentos , text = "|dT/dt|<", variable = self.checkboxCondiciondTdt, command = self.botonCheckboxCondiciondTdt).grid(row = 12, column = 7, sticky =E)
		self.entrydTdtSalida =ttk.Entry(self.frameExperimentos, width=5, textvariable = self.dTdtSalida)
		self.entrydTdtSalida.grid(column=	8, row = 12, sticky =(W,E))
		self.entrydTdtSalida.config(state = DISABLED)


		ttk.Checkbutton(self.frameExperimentos , text = "|dp/dt|<", variable = self.checkboxCondiciondpdt, command = self.botonCheckboxCondiciondpdt).grid(row = 12, column = 9, sticky =E)
		self.entrydpdtSalida =ttk.Entry(self.frameExperimentos, width=5, textvariable = self.dpdtSalida)
		self.entrydpdtSalida.grid(column=	10, row = 12, sticky =(W,E))
		self.entrydpdtSalida.config(state = DISABLED)

		ttk.Checkbutton(self.frameExperimentos , text = "|dm/dt|<", variable = self.checkboxCondiciondmdt, command = self.botonCheckboxCondiciondmdt).grid(row = 12, column = 11, sticky =E)
		self.entrydmdtSalida =ttk.Entry(self.frameExperimentos, width=5, textvariable = self.dmdtSalida)
		self.entrydmdtSalida.grid(column=	12, row = 12, sticky =(W,E))
		self.entrydmdtSalida.config(state = DISABLED)

	def armaVentanaGraficos(self):
		self.frameGraficos = ttk.Frame(self.grp, padding="5 5 5 5")
		self.frameGraficos.grid(column=0, row=0, sticky=(N, W, E, S))

		self.nbGrp = ttk.Notebook(self.frameGraficos)

		self.nbGrp.grid(row=0, column = 0, rowspan=13, columnspan=15)
		
		self.MasavsTiempo = ttk.Frame(self.nbGrp)
		self.MasavsTemper = ttk.Frame(self.nbGrp)
		self.MasavsPresio = ttk.Frame(self.nbGrp)
		self.TempvsTiempo = ttk.Frame(self.nbGrp)
		self.PresvsTiempo = ttk.Frame(self.nbGrp)
		self.FlujvsTiempo = ttk.Frame(self.nbGrp)


		self.nbGrp.add(self.MasavsTiempo , text = "Masa y tiempo")
		self.nbGrp.add(self.MasavsTemper , text = "Masa y temperatura")
		self.nbGrp.add(self.MasavsPresio , text = "Masa y presión")
		self.nbGrp.add(self.TempvsTiempo , text = "Temperatura y tiempo")
		self.nbGrp.add(self.PresvsTiempo , text = "Presión y tiempo")
		self.nbGrp.add(self.FlujvsTiempo , text = "Flujos y tiempo")

		self.canvasMasavsTiempo = Canvas(self.MasavsTiempo, width=1000, height=540)
		self.canvasMasavsTemper = Canvas(self.MasavsTemper, width=1000, height=540)
		self.canvasMasavsPresio = Canvas(self.MasavsPresio, width=1000, height=540)
		self.canvasTempvsTiempo = Canvas(self.TempvsTiempo, width=1000, height=540)
		self.canvasPresvsTiempo = Canvas(self.PresvsTiempo, width=1000, height=540)
		self.canvasFlujvsTiempo = Canvas(self.FlujvsTiempo, width=1000, height=540)

		self.canvasMasavsTiempo.grid(row=0, column=0, columnspan = 15, rowspan =15)
		self.canvasMasavsTemper.grid(row=0, column=0, columnspan = 15, rowspan =15)
		self.canvasMasavsPresio.grid(row=0, column=0, columnspan = 15, rowspan =15)
		self.canvasTempvsTiempo.grid(row=0, column=0, columnspan = 15, rowspan =15)
		self.canvasPresvsTiempo.grid(row=0, column=0, columnspan = 15, rowspan =15)
		self.canvasFlujvsTiempo.grid(row=0, column=0, columnspan = 15, rowspan =15)	

		self.progressBarGrp = ttk.Progressbar(self.frameGraficos, orient="horizontal", length=1000, mode="determinate")
		self.progressBarGrp.grid(row = 18, column = 0, columnspan = 15)

		ttk.Label(self.frameGraficos, text="M [mg]:").grid( column=0, row=16, sticky=(E))
		ttk.Label(self.frameGraficos, text="T [°C]:").grid( column=2, row=16, sticky=(E))
		ttk.Label(self.frameGraficos, text="t (Tot)[s]:").grid( column=4, row=16, sticky=(E))
		ttk.Label(self.frameGraficos, text="P [torr]:").grid( column=6, row=16, sticky=(E))
		ttk.Label(self.frameGraficos, text="F [sccm]:").grid( column=8, row=16, sticky=(E))

		ttk.Label(self.frameGraficos, text="dp/dt [torr/s]:").grid( column=0, row=17, sticky=(E))
		ttk.Label(self.frameGraficos, text="dT/dt [°C/min]:").grid( column=2, row=17, sticky=(E))
		#ttk.Label(self.frameGraficos, text="dm/dt:").grid( column=4, row=17, sticky=(W, E))

		ttk.Label(self.frameGraficos, textvariable = self.dpdt).grid(column=1, row=17, sticky=(W, E))
		ttk.Label(self.frameGraficos, textvariable = self.dTdt).grid(column=3, row=17, sticky=(W, E))
		#ttk.Label(self.frameGraficos, textvariable = self.dmdt).grid(column=5, row=17, sticky=(W, E))

		ttk.Label(self.frameGraficos, text = "X:").grid(column=5, row=17, sticky=(W,E))
		ttk.Entry(self.frameGraficos, textvariable = self.xmin, width=3).grid(column=6, row=17, sticky=(W,E))
		ttk.Entry(self.frameGraficos, textvariable = self.xmax, width=3).grid(column=7, row=17, sticky=(W,E))

		ttk.Label(self.frameGraficos, text = "Y:").grid(column=9, row=17, sticky=(W,E))
		ttk.Entry(self.frameGraficos, textvariable = self.ymin, width=3).grid(column=10, row=17, sticky=(W,E))
		ttk.Entry(self.frameGraficos, textvariable = self.ymax, width=3).grid(column=11, row=17, sticky=(W,E))
		
		ttk.Checkbutton(self.frameGraficos, variable = self.rangoCustomX).grid(column=4, row=17, sticky=(E))
		ttk.Checkbutton(self.frameGraficos, variable = self.rangoCustomY).grid(column=8, row=17, sticky=(E))


		ttk.Label(self.frameGraficos, textvariable = self.masa).grid( column=1, row=16, sticky=(W, E))
		ttk.Label(self.frameGraficos, textvariable = self.tempMuestra).grid( column=3, row=16, sticky=(W, E))
		ttk.Label(self.frameGraficos, textvariable = self.tiempo).grid( column=5, row=16, sticky=(W, E))
		ttk.Label(self.frameGraficos, textvariable = self.presionAlta).grid(column=7, row=16, sticky=(W, E))
		ttk.Label(self.frameGraficos, textvariable = self.caudalMasa1).grid(column=9, row=16, sticky=(W, E))
		ttk.Label(self.frameGraficos, textvariable = self.caudalMasa2).grid(column=10, row=16, sticky=(W, E))
		ttk.Label(self.frameGraficos, textvariable = self.caudalMasa3).grid(column=11, row=16, sticky=(W, E))

		ttk.Label(self.frameGraficos, text = "t (subExp):").grid(column=12, row=16, sticky=(E))
		ttk.Label(self.frameGraficos, text = str(self.experimentoVariable.tiempoSubExp)).grid(column=13, row=16, sticky=(W))
		ttk.Label(self.frameGraficos, text = "N (subExp):").grid(column=12, row=17, sticky=(E))
		ttk.Label(self.frameGraficos, text = str(self.experimentoVariable.subExpCorriendo)).grid(column=13, row=17, sticky=(W))

	def armaVentanaLogs(self, kill):
		self.frameLogs = ttk.Frame(self.logs, padding="10 10 12 12")
		self.frameLogs.grid(column=0, row=0, sticky=(N, W, E, S))

		self.arbolLog = ttk.Treeview(self.frameLogs, height=28, columns = ("Fecha", "Hora", "Archivo","Descripción", "Carpeta"))
		self.arbolLog.grid(column=0, row=0, rowspan = 5, columnspan = 3)
		
		self.arbolLog.heading("#0", text = "N°")
		self.arbolLog.column("#0", minwidth=0, width=0)
		self.arbolLog.heading("Fecha", text = "Fecha")
		self.arbolLog.column("Fecha", minwidth=0, width=60)
		self.arbolLog.heading("Hora", text = "Hora")
		self.arbolLog.column("Hora", minwidth=0, width=60)
		self.arbolLog.heading("Archivo", text = "Archivo")
		self.arbolLog.column("Archivo", minwidth=0, width=70)
		self.arbolLog.heading("Descripción", text = "Descripción")
		self.arbolLog.column("Descripción", minwidth=0, width=120)
		self.arbolLog.heading("Descripción", text = "Descripción")
		self.arbolLog.column("Descripción", minwidth=0, width=340)
		self.arbolLog.heading("Carpeta", text = "Carpeta")
		self.arbolLog.column("Carpeta", minwidth=0, width=340)


		ttk.Button(self.frameLogs, text="Ver gráficas", 		command=self.botonVerGraficas).grid(column=0, row=6, sticky=E)
		ttk.Button(self.frameLogs, text="Repetir experimento", 	command=self.botonRepetirExperimento).grid(column=1, row=6)
		ttk.Button(self.frameLogs, text="Ver log", 	command=self.botonVerLog).grid(column=2, row=6, sticky=W)


		ttk.Button(self.frameLogs, text = "salir", command = kill).grid(column=1, row=7)

		with open('experimentLog.dat', 'r') as f:
			for line in f:
				exp  = line.split("\t")
				self.arbolLog.insert("", END, text="", values=(exp[0],
															   exp[1],
															   exp[2], 
															   exp[3],
															   exp[4]))

	def inicializaVariables(self):

		self.masa = DoubleVar()
		self.masaFicticia = DoubleVar(value = 0)

		self.presionBaja = DoubleVar()
		self.presionAlta = DoubleVar()
		self.tempMuestra = DoubleVar()
		self.filenameCarpeta = StringVar()

		self.carpetaFlag = BooleanVar(value = False)



		self.tiempoPC = DoubleVar()
		self.presionBuscadaVar = DoubleVar()
		self.flujoBuscadoVar = DoubleVar()
		self.masaVector = []
		self.tiempoVector = []

		self.xmin	= DoubleVar(value = 0)
		self.xmax	= DoubleVar(value = 1)
		self.ymin	= DoubleVar(value = 0)
		self.ymax 	= DoubleVar(value = 1)

		self.rangoCustomX = BooleanVar(value = False)
		self.rangoCustomY = BooleanVar(value = False)

		self.presionBajaVector = []
		self.presionAltaVector = []
		self.tempMuestraVector = []
		self.caudalMasa1Vector = []
		self.caudalMasa2Vector = []
		self.caudalMasa3Vector = []

		self.tempSetVector = []
		self.presSetVector = []
		self.cau1SetVector = []
		self.cau2SetVector = []
		self.cau3SetVector = []
		
		self.tempHorno 	= DoubleVar()
		self.tempBaño	= DoubleVar()

		self.alphaVar = DoubleVar(value = 0.05)
		self.betaVar = DoubleVar(value = 2)
		self.gammaVar = DoubleVar(value = 0)
		self.dpmaxVar = DoubleVar(value = 0.8)
		self.tmaxVar = DoubleVar(value = 4.0)
		self.deltaApMinVar = DoubleVar(value = 0.1)

		self.controlo = BooleanVar()
		
		self.caudalMasa1 = DoubleVar()
		self.caudalMasa2 = DoubleVar()
		self.caudalMasa3 = DoubleVar()
		
		self.outMasa1 	= DoubleVar()
		self.outMasa2 	= DoubleVar()
		self.outMasa3 	= DoubleVar()
		
		self.estadoV1 	= BooleanVar()
		self.estadoV2 	= BooleanVar()
		self.estadoV3 	= BooleanVar()
		self.estadoV4 	= BooleanVar()
		self.estadoV5 	= BooleanVar()
		self.estadoV6 	= BooleanVar()
		self.estadoV7 	= BooleanVar()
		self.estadoV8 	= BooleanVar()
		self.estadoV9 	= BooleanVar()
		self.estadoV10 	= BooleanVar()
		self.estadoV11	= BooleanVar()
		self.estadoV12	= BooleanVar()
		self.estadoV13 	= BooleanVar()
		self.estadoV14 	= BooleanVar()
		self.estadoV15 	= BooleanVar()

		self.tempInicial = DoubleVar()
		self.tempFinal = DoubleVar()
		self.presionInicial = DoubleVar()
		self.presionFinal = DoubleVar()
		self.flujo1Inicial = DoubleVar()
		self.flujo2Inicial = DoubleVar()
		self.flujo3Inicial = DoubleVar()
		self.flujo1Final = DoubleVar()
		self.flujo2Final = DoubleVar()
		self.flujo3Final = DoubleVar()
		self.tiempoTotal = DoubleVar(value = 30)
		self.tiempoPaso = DoubleVar(value = 2)
		self.descripcion = StringVar(value = "Agustín")
		self.nombreArchivo = StringVar(value = "Muestra")

		self.tiempo = DoubleVar(value = 0.0)

		self.tempSet = DoubleVar()
		self.presSet = DoubleVar()
		self.cau1Set = DoubleVar()
		self.cau2Set = DoubleVar()
		self.cau3Set = DoubleVar()

		self.checkboxPresion = IntVar()
		self.checkboxTemperatura = IntVar()
		self.checkboxFlujo1 = IntVar()
		self.checkboxFlujo2 = IntVar()
		self.checkboxFlujo3 = IntVar()
		self.checkboxFlujoHorno = IntVar()
		self.checkboxFlujoVenteo = IntVar()
		self.checkboxFlujoVenteoHorno = IntVar()

		self.checkboxCondiciont = IntVar(value = 1)
		self.tiempoSalida = DoubleVar()
		self.checkboxCondicionT = IntVar()
		self.tempSalida = DoubleVar()
		self.checkboxCondicionP = IntVar()
		self.presSalida  = DoubleVar()
		self.checkboxCondiciondpdt = IntVar()
		self.checkboxCondiciondTdt = IntVar()
		self.checkboxCondiciondmdt = IntVar()
		self.dpdtSalida = DoubleVar()
		self.dTdtSalida = DoubleVar()
		self.dmdtSalida = DoubleVar()

		self.dpdt = DoubleVar()
		self.dTdt = DoubleVar()
		self.dmdt = DoubleVar()

	def actualizaValores(self, *args):
		try:
			self.presionAlta.set(midePresionAlta(5))
			self.presionBaja.set(midePresionBaja(5))
			self.tempMuestra.set(mideTemperaturaMuestra(5))
		except ValueError:
			pass

	def actualizaValoresMasa(self, *args):
		try:
			self.caudalMasa1.set(mideCaudalMasico(5,1))
			self.caudalMasa2.set(mideCaudalMasico(5,2))
			self.caudalMasa3.set(mideCaudalMasico(5,3))
		except ValueError:
			pass

	def botonVerGraficas(self):
		vector_values = self.arbolLog.item(self.arbolLog.selection())["values"]

		directory = vector_values[4]
		os.startfile(directory)
		pass

	def botonRepetirExperimento(self):
		self.limpiaSubExp()
		vector_values = self.arbolLog.item(self.arbolLog.selection())["values"]
		print(vector_values)
		conf_file = vector_values[4]+"/"+vector_values[2]+".conf"

		self.descripcion.set(vector_values[3])
		self.nombreArchivo.set(vector_values[2])

		with open(conf_file, "r") as f:
			for line in f:
				print(line[2])
				valores = line.split("\t")
				dictionary = eval(valores[18])
				sExp = subExp(float(valores[2]),  	float(valores[3]), 
							  float(valores[1]), 	float(valores[0]), 
							  float(valores[4]), 	float(valores[5]), 	 
							  float(valores[6]), 	float(valores[7]), 	float(valores[8]),  
							  float(valores[9]), 	float(valores[10]), float(valores[11]),
							  self.queuePressure,
							  float(valores[12]),	float(valores[13]),	float(valores[14]),
							  float(valores[15]),	float(valores[16]),	float(valores[17]),
							  dictionary)
				self.experimentoVariable.archivo = 'ArchivoGenerico.dat'

				self.arbolExperimentos.insert("", END, text=str(len(self.experimentoVariable.expLista)), values=(
																		sExp.tempInicial, 
																		sExp.tempFinal, 
																		sExp.presionInicial, 
																		sExp.presionFinal, 
																		sExp.flujoInicial1,
																		sExp.flujoInicial2,
																		sExp.flujoInicial3, 
																		sExp.flujoFinal1, 
																		sExp.flujoFinal2,
																		sExp.flujoFinal3, 
																		sExp.tiempoTotal, 
																		sExp.tiempoPaso,
																		sExp.queuePressure))

				self.experimentoVariable.añadeSubExp(sExp)

		self.actualizaGraficosVentanaExperimento()
		self.nb.select(self.exp)

	def botonVerLog(self):
		
		vector_values = self.arbolLog.item(self.arbolLog.selection())["values"]
		conf_file = vector_values[4]+"/ExperimentoLog.txt"
		os.startfile(conf_file)
		pass

	def botonTemperaturaHorno(self, *args):
		try:
			value = float(self.tempHorno.get())
			seteaTemperaturaHorno(value)
		except ValueError:
			pass

	def botonTemperaturaBaño(self, *args):
		try:
			value = float(self.tempBaño.get())
			seteaTemperaturaHorno(value)
		except ValueError:
			pass

	def botonMFC1(self, *args):
		try:
			value = float(self.outMasa1.get())
			seteaCaudalMasico(value, 1)
		except ValueError:
			pass

	def botonMFC2(self, *args):
		try:
			value = float(self.outMasa2.get())
			seteaCaudalMasico(value, 2)
		except ValueError:
			pass

	def botonMFC3(self, *args):
		try:
			value = float(self.outMasa3.get())
			seteaCaudalMasico(value, 3)
		except ValueError:
			pass

	def boton10(self):
		cierraValvula("PCC")
		abreValvula("PCO")

	def boton01(self):
		cierraValvula("PCO")
		abreValvula("PCC")
		pass

	def boton00(self):
		cierraValvula("PCC")
		cierraValvula("PCO")

	def botonCargar(self):

		fname = filedialog.askopenfilename(initialdir = os.getcwd()+"/", title = "Abrir archivo", filetypes = [("conf files","*.conf"), ("conf files", "*.CONF"), ("all files", "*.*")])

		try:
			with open(fname, "r") as f:
				for line in f:
					print(line[2])
					valores = line.split("\t")
					dictionary = eval(valores[18])
					sExp = subExp(float(valores[2]),  	float(valores[3]), 
								  float(valores[1]), 	float(valores[0]), 
								  float(valores[4]), 	float(valores[5]), 	 
								  float(valores[6]), 	float(valores[7]), 	float(valores[8]),  
								  float(valores[9]), 	float(valores[10]), float(valores[11]),
								  self.queuePressure,
								  float(valores[12]),	float(valores[13]),	float(valores[14]),
								  float(valores[15]),	float(valores[16]),	float(valores[17]),
								  dictionary)
					self.experimentoVariable.archivo = 'ArchivoGenerico.dat'

					self.arbolExperimentos.insert("", END, text=str(len(self.experimentoVariable.expLista)), values=(
																			sExp.tempInicial, 
																			sExp.tempFinal, 
																			sExp.presionInicial, 
																			sExp.presionFinal, 
																			sExp.flujoInicial1,
																			sExp.flujoInicial2,
																			sExp.flujoInicial3, 
																			sExp.flujoFinal1, 
																			sExp.flujoFinal2,
																			sExp.flujoFinal3, 
																			sExp.tiempoTotal, 
																			sExp.tiempoPaso,
																			sExp.queuePressure))

					self.experimentoVariable.añadeSubExp(sExp)

			self.actualizaGraficosVentanaExperimento()
			self.nb.select(self.exp)

		except FileNotFoundError:
			pass

	def botonGuardar(self):

		fname = filedialog.asksaveasfilename(initialdir = os.getcwd()+"/", title = "Guardar archivo", filetypes = [("conf files","*.conf"), ("conf files", "*.CONF"), ("all files", "*.*")])

		with open(fname+ ".conf", "w") as f:
			for subExp in self.experimentoVariable.expLista:
				f.write(str(subExp.tiempoPaso)+"\t")
				f.write(str(subExp.tiempoTotal)+"\t")
				f.write(str(subExp.tempInicial) +"\t")
				f.write(str(subExp.tempFinal)+"\t")
				f.write(str(subExp.presionInicial)+"\t")
				f.write(str(subExp.presionFinal) +"\t")
				f.write(str(subExp.flujoInicial1)+"\t")
				f.write(str(subExp.flujoInicial2)+"\t")
				f.write(str(subExp.flujoInicial3)+"\t")
				f.write(str(subExp.flujoFinal1)+"\t")
				f.write(str(subExp.flujoFinal2)+"\t")
				f.write(str(subExp.flujoFinal3)+"\t")
				f.write(str(subExp.checkboxFlujo1)+"\t")
				f.write(str(subExp.checkboxFlujo2)+"\t")
				f.write(str(subExp.checkboxFlujo3)+"\t")
				f.write(str(subExp.checkboxFlujoVenteo)+"\t")
				f.write(str(subExp.checkboxFlujoHorno)+"\t")
				f.write(str(subExp.checkboxFlujoVenteoHorno)+"\t")
				f.write(str(subExp.condicion_salida) + "\n")

	def botonCheckboxPresion(self):
		if(self.checkboxPresion.get() == 0):
			self.entryPresInicial.config(state=DISABLED)
			self.entryPresFinal.config(state=DISABLED)
			self.presionInicial.set(0)
			self.presionFinal.set(0)
		else:
			self.entryPresInicial.config(state=NORMAL)
			self.entryPresFinal.config(state=NORMAL)

	def botonCheckboxTemperatura(self):
		if(self.checkboxTemperatura.get() == 0):
			self.entryTempInicial.config(state=DISABLED)
			self.entryTempFinal.config(state=DISABLED)
			self.tempInicial.set(0)
			self.tempFinal.set(0)
		else:
			self.entryTempInicial.config(state=NORMAL)
			self.entryTempFinal.config(state=NORMAL)

	def botonCheckboxFlujo1(self):
		if(self.checkboxFlujo1.get() == 0):
			self.flujoInicial1Entry.config(state=DISABLED)
			self.flujoFinal1Entry.config(state=DISABLED)
			self.flujo1Inicial.set(0)
			self.flujo1Final.set(0)
		else:
			self.flujoInicial1Entry.config(state=NORMAL)
			self.flujoFinal1Entry.config(state=NORMAL)

	def botonCheckboxFlujo2(self):
		if(self.checkboxFlujo2.get() == 0):
			self.flujoInicial2Entry.config(state=DISABLED)
			self.flujoFinal2Entry.config(state=DISABLED)
			self.flujo2Inicial.set(0)
			self.flujo2Final.set(0)
		else:
			self.flujoInicial2Entry.config(state=NORMAL)
			self.flujoFinal2Entry.config(state=NORMAL)

	def botonCheckboxFlujo3(self):
		if(self.checkboxFlujo3.get() == 0):
			self.flujoInicial3Entry.config(state=DISABLED)
			self.flujoFinal3Entry.config(state=DISABLED)
			self.flujo3Inicial.set(0)
			self.flujo3Final.set(0)
		else:
			self.flujoInicial3Entry.config(state=NORMAL)
			self.flujoFinal3Entry.config(state=NORMAL)

	def botonCheckboxCondicionP(self):
		if(self.checkboxCondicionP.get() == 0):
			self.entryPresSalida.config(state=DISABLED)
			self.presSalida.set(0)
		else:
			self.entryPresSalida.config(state=NORMAL)

	def botonCheckboxCondicionT(self):
		if(self.checkboxCondicionT.get() == 0):
			self.entryTempSalida.config(state=DISABLED)
			self.tempSalida.set(0)
		else:
			self.entryTempSalida.config(state=NORMAL)

	def botonCheckboxCondiciont(self):
		pass
		pass

	def botonCheckboxCondiciondpdt(self):
		if(self.checkboxCondiciondpdt.get() == 0):
			self.entrydpdtSalida.config(state=DISABLED)
			self.dpdtSalida.set(0)
		else:
			self.entrydpdtSalida.config(state=NORMAL)

	def botonCheckboxCondiciondmdt(self):
		if(self.checkboxCondiciondmdt.get() == 0):
			self.entrydmdtSalida.config(state=DISABLED)
			self.dmdtSalida.set(0)
		else:
			self.entrydmdtSalida.config(state=NORMAL)

	def botonCheckboxCondiciondTdt(self):
		if(self.checkboxCondiciondTdt.get() == 0):
			self.entrydTdtSalida.config(state=DISABLED)
			self.dTdtSalida.set(0)
		else:
			self.entrydTdtSalida.config(state=NORMAL)

	def botonSeleccionarCarpeta(self):


		fname = filedialog.askdirectory(initialdir = os.getcwd()+"/", title = "Seleccionar Carpeta")
		self.carpetaFlag.set(True)
		self.filenameCarpeta.set(fname)

	def abrirPC(self, t):
		self.queuePressure.put(["open", t])
		pass

	def cerrarPC(self, t):
		self.queuePressure.put(["close", t])
		pass

	def botonMasa(self, *args):
		try:
			value = float(mideBalanza())
			print(value)
			self.masa.set(value)
		except ValueError:
			pass

	def limpiaSubExp(self, *args):

		for item in self.arbolExperimentos.get_children():

			self.arbolExperimentos.delete(item)

		self.experimentoVariable = None
		self.experimentoVariable = Exp(self.queue)


		self.actualizaGraficosVentanaExperimento()

	def saltaSubExp(self, *args):
		self.experimentoVariable.saltaSubExp = 1
		pass

	def modificaSubExp(self, *args):

		selected_items = self.arbolExperimentos.selection()

		subExperimento = subExp(self.tempInicial.get(), 
							    self.tempFinal.get(), 
							    self.tiempoTotal.get(), 
							    self.tiempoPaso.get(),
			    			    self.presionInicial.get(), 
			    			    self.presionFinal.get(), 
			    			    self.flujo1Inicial.get(),
							    self.flujo2Inicial.get(),
							    self.flujo3Inicial.get(), 
							    self.flujo1Final.get(), 
							    self.flujo2Final.get(),
							    self.flujo3Final.get(),
								self.queuePressure,
								self.checkboxFlujo1.get(),
								self.checkboxFlujo2.get(),
								self.checkboxFlujo3.get(),
								self.checkboxFlujoHorno.get(),
								self.checkboxFlujoVenteoHorno.get(),
								self.checkboxFlujoVenteo.get(),
								self.condicionSalida())

		self.experimentoVariable.expLista[int(self.arbolExperimentos.item(selected_items)['text'])] = subExperimento 

		self.arbolExperimentos.item(selected_items[0],values=(self.tempInicial.get(), 
															self.tempFinal.get(), 
															self.presionInicial.get(), 
															self.presionFinal.get(), 
															self.flujo1Inicial.get(),
															self.flujo2Inicial.get(),
															self.flujo3Inicial.get(), 
															self.flujo1Final.get(), 
															self.flujo2Final.get(),
															self.flujo3Final.get(), 
															self.tiempoTotal.get(), 
															self.tiempoPaso.get()) )


		self.actualizaGraficosVentanaExperimento()
	
	def añadeSubExp(self, *args):

		if(self.checkboxCondicionP.get()+
			self.checkboxCondicionT.get()+
			self.checkboxCondiciont.get()+
			self.checkboxCondiciondpdt.get()+
			self.checkboxCondiciondTdt.get()+
			self.checkboxCondiciondmdt.get() == 0):
			messagebox.showinfo("Error", "Alguna condición de salida tiene que tener")
			return None
		if(self.nombreArchivo.get()==""):
			messagebox.showinfo("Error", "Especifique un nombre de archivo")
			return None
		if(self.tiempoPaso.get() < 1.0):
			messagebox.showinfo("Error", "El tiempo mínimo de medición es un segundo")
			return None


		try:
			
			subExperimento = subExp(self.tempInicial.get(), 
										 self.tempFinal.get(), 
										 self.tiempoTotal.get(), 
										 self.tiempoPaso.get(),
			    						 self.presionInicial.get(), 
			    						 self.presionFinal.get(), 
			    						 self.flujo1Inicial.get(),
										 self.flujo2Inicial.get(),
										 self.flujo3Inicial.get(), 
										 self.flujo1Final.get(), 
										 self.flujo2Final.get(),
										 self.flujo3Final.get(),
										 self.queuePressure,
										 self.checkboxFlujo1.get(),
										 self.checkboxFlujo2.get(),
										 self.checkboxFlujo3.get(),
										 self.checkboxFlujoHorno.get(),
										 self.checkboxFlujoVenteoHorno.get(),
										 self.checkboxFlujoVenteo.get(),
										 self.condicionSalida())

			self.arbolExperimentos.insert("", END, text=str(len(self.experimentoVariable.expLista)), values=(
																					self.tempInicial.get(), 
																					self.tempFinal.get(), 
																					self.presionInicial.get(), 
																					self.presionFinal.get(), 
																					self.flujo1Inicial.get(),
																					self.flujo2Inicial.get(),
																					self.flujo3Inicial.get(), 
																					self.flujo1Final.get(), 
																					self.flujo2Final.get(),
																					self.flujo3Final.get(), 
																					self.tiempoTotal.get(), 
																					self.tiempoPaso.get(),
																					self.queuePressure))
		
	
			self.experimentoVariable.añadeSubExp(subExperimento)
			self.experimentoVariable.archivo = self.nombreArchivo.get()
			self.actualizaGraficosVentanaExperimento()
		except ZeroDivisionError:
			messagebox.showinfo("Error", "El paso del tiempo debe ser distinto de cero")
	
	def remueveSubExp(self, *args):

		selected_items = self.arbolExperimentos.selection()

		for selected_item in selected_items:

			self.experimentoVariable.expLista.pop(int(self.arbolExperimentos.item(selected_item)['text']))

			unselected_items = [x for x in self.arbolExperimentos.get_children() if x not in selected_item]
			for unselected_item in unselected_items:
				if (int(self.arbolExperimentos.item(selected_item)['text']) < int(self.arbolExperimentos.item(unselected_item)['text'])):
					self.arbolExperimentos.item(unselected_item, text = str(int(self.arbolExperimentos.item(unselected_item)['text']) - 1 ))
			self.arbolExperimentos.delete(selected_item)


		self.actualizaGraficosVentanaExperimento()
	
	def ejecutaExp(self, *args):
		suma = 0

		if(self.carpetaFlag.get()==False):
			messagebox.showinfo("Error", "Seleccioná una carpeta")
			return 0

		self.armaExperimentoLog()
		for i in self.experimentoVariable.expLista:
			suma += i.tiempoTotal


		self.experimentoVariable.correExperimento = 1
		self.experimentoVariable.correExperimentoPresion = 0
		self.progressBar.start(int(suma*10))
		self.progressBarGrp.start(int(suma*10))

	def ejecutaExpPresion(self, *args):

		self.experimentoVariable.correExperimentoPresion = 1
		self.experimentoVariable.correExperimento = 0

	def ejecutaDefinePosicion(self, *args):
		self.experimentoVariable.archivo = "auxiliarTau.dat"
		self.experimentoVariable.definePosicion = 1
		print('horizontal')
		pass

	def ejecutaBuscaPosicion(self, *args):
		self.experimentoVariable.presionReducidaBuscada = self.presionBuscadaVar.get()*(50/self.flujoBuscadoVar.get())**0.937
		self.experimentoVariable.buscaPosicion = 1
		print('vertical')
		pass

	def procesoLlegando(self):
		while(self.queue.qsize()):
			try:
				mensaje = self.queue.get(0)

				self.masa.set(mensaje["masa"])
				self.presionBaja.set(mensaje["baja"]) 
				self.presionAlta.set(mensaje["alta"]) 
				self.tempMuestra.set(mensaje["temp"]) 
				self.caudalMasa1.set(mensaje["cau1"]) 
				self.caudalMasa2.set(mensaje["cau2"]) 
				self.caudalMasa3.set(mensaje["cau3"])
				self.tiempo.set(mensaje["tiem"])

				self.tempSet.set(mensaje["tset"])
				self.presSet.set(mensaje["pset"])

				self.cau1Set.set(mensaje["1set"])
				self.cau2Set.set(mensaje["2set"])
				self.cau3Set.set(mensaje["3set"])

				self.dpdt.set(mensaje['dpdt'])
				self.dTdt.set(mensaje['dTdt'])
				self.dmdt.set(mensaje['dmdt'])


				self.actualizaGraficosVentanaGraficos() 
				
			except queue.Empty:
				pass

	def draw_figure(self, canvas, figure, loc=(0, 0)):
	
		figure_canvas_agg = FigureCanvasAgg(figure)
		figure_canvas_agg.draw()
		figure_x, figure_y, figure_w, figure_h = figure.bbox.bounds
		figure_w, figure_h = int(figure_w), int(figure_h)
		photo = PhotoImage(master=canvas, width=figure_w, height=figure_h)
	
		# Position: convert from top-left anchor to center anchor
		canvas.create_image(loc[0] + figure_w/2, loc[1] + figure_h/2, image=photo)
	
		# Unfortunately, there's no accessor for the pointer to the native renderer
		tkagg.blit(photo, figure_canvas_agg.get_renderer()._renderer, colormode=2)
	
		# Return a handle which contains a reference to the photo object
		# which must be kept live or else the picture disappears
		return photo

	def guardaGraficosyArchivos(self):

		now = datetime.datetime.now()
		fname = self.filenameCarpeta.get()+"/"
		fnameExp = fname + self.nombreArchivo.get()+".conf"
		fnameDat = fname + self.nombreArchivo.get()+".dat"
		fnameMvt = fname + "Mvt.png"
		fnameMvT = fname + "MvT.png"
		fnameMvP = fname + "MvP.png"
		fnameTvt = fname + "Tvt.png"
		fnamePvt = fname + "Pvt.png"
		fnameFvt = fname + "Fvt.png"


		self.armaExperimentoLog()

		os.makedirs(os.path.dirname(fname), exist_ok=True)
		with open(fnameExp, "w") as f:
			for subExp in self.experimentoVariable.expLista:
				f.write(str(subExp.tiempoPaso)+"\t")
				f.write(str(subExp.tiempoTotal)+"\t")
				f.write(str(subExp.tempInicial) +"\t")
				f.write(str(subExp.tempFinal)+"\t")
				f.write(str(subExp.presionInicial)+"\t")
				f.write(str(subExp.presionFinal) +"\t")
				f.write(str(subExp.flujoInicial1)+"\t")
				f.write(str(subExp.flujoInicial2)+"\t")
				f.write(str(subExp.flujoInicial3)+"\t")
				f.write(str(subExp.flujoFinal1)+"\t")
				f.write(str(subExp.flujoFinal2)+"\t")
				f.write(str(subExp.flujoFinal3)+"\t")
				f.write(str(subExp.checkboxFlujo1)+"\t")
				f.write(str(subExp.checkboxFlujo2)+"\t")
				f.write(str(subExp.checkboxFlujo3)+"\t")
				f.write(str(subExp.checkboxFlujoVenteo)+"\t")
				f.write(str(subExp.checkboxFlujoHorno)+"\t")
				f.write(str(subExp.checkboxFlujoVenteoHorno)+"\t")
				f.write(str(subExp.condicion_salida) + "\n")
				
		shutil.copy(str(self.experimentoVariable.archivo), fnameDat)

		self.figMvt.savefig(fnameMvt)
		self.figMvT.savefig(fnameMvT)
		self.figMvP.savefig(fnameMvP)
		self.figPvt.savefig(fnamePvt)
		self.figTvt.savefig(fnameTvt)
		self.figFvt.savefig(fnameFvt)



		self.arbolLog.insert("", END, text=str(len(self.experimentoVariable.expLista)), values=(str(now.year)+" "+str(now.month)+" "+str(now.day),
																					str(now.hour)+"h"+str(now.minute)+"m",
																					self.nombreArchivo.get(), 
																					self.descripcion.get(),
																					self.filenameCarpeta.get()))



		self.progressBar.stop()
		self.progressBarGrp.stop()

		self.masaVector = []
		self.tiempoVector = []
		self.presionBajaVector = []
		self.presionAltaVector = []
		self.tempMuestraVector = []
		self.caudalMasa1Vector = []
		self.caudalMasa2Vector = []
		self.caudalMasa3Vector = []

		self.tempSetVector = []
		self.presSetVector = []
		self.cau1SetVector = []
		self.cau2SetVector = []
		self.cau3SetVector = []

		with open('experimentLog.dat', "a") as f:
			f.write("\n"+str(now.year)+" "+str(now.month)+" "+str(now.day)+"\t"+str(now.hour)+"h"+str(now.minute)+"m"+"\t"+self.nombreArchivo.get()+"\t"+self.descripcion.get()+"\t"+self.filenameCarpeta.get())
	
	def actualizaGraficosVentanaExperimento(self):


		tiempo = []
		temperatura = []
		presion = []
		flujo1 = []
		flujo2 = []
		flujo3 = []
		tiempoInicial = 0
		
		for subExp in self.experimentoVariable.expLista:
			for paso in range(int(subExp.pasos)):
				tiempo.append(paso * subExp.tiempoPaso + tiempoInicial)		
				temperatura.append(paso * subExp.tempPaso + subExp.tempInicial)		
				presion.append(paso * subExp.presionPaso + subExp.presionInicial)		
				flujo1.append(paso * subExp.flujoPaso1 + subExp.flujoInicial1)		
				flujo2.append(paso * subExp.flujoPaso2 + subExp.flujoInicial2)		
				flujo3.append(paso * subExp.flujoPaso3 + subExp.flujoInicial3)
			tiempoInicial += subExp.tiempoTotal
		

		fig = mpl.figure.Figure(figsize=(7.5,3), frameon = True)
		ax = fig.add_subplot(111)		
		ax.set_xlabel("Tiempo [s]")
		ax.xaxis.set_label_position('top') 
		ax.set_ylabel("Temperatura [°C]")
		ax.grid(b=True)
		ax.plot(np.asarray(tiempo), np.asarray(temperatura))


		self.figTvst = self.draw_figure(self.canvasTvst, fig, loc=(0, 0))

		fig = mpl.figure.Figure(figsize=(7.5,3), frameon = True)
		ax = fig.add_subplot(111)		
		ax.set_xlabel("Tiempo [s]")
		ax.xaxis.set_label_position('top') 
		ax.set_ylabel("Presion [torr]")
		ax.grid(b=True)
		ax.set_axis_on()
		ax.plot(np.asarray(tiempo), np.asarray(presion))

		self.figPvst = self.draw_figure(self.canvasPvst, fig, loc=(0, 0))

		fig = mpl.figure.Figure(figsize=(7.5,3), frameon = True)
		ax = fig.add_subplot(111)		
		ax.set_xlabel("Tiempo [s]")
		ax.xaxis.set_label_position('top') 
		ax.set_ylabel("Caudal [sccm]")
		ax.grid(b=True)
		ax.plot(np.asarray(tiempo), np.asarray(flujo1), label = "1, Medido")
		ax.plot(np.asarray(tiempo), np.asarray(flujo2), label = "2, Medido")
		ax.plot(np.asarray(tiempo), np.asarray(flujo3), label = "3, Medido")

		self.figFvst = self.draw_figure(self.canvasFvst, fig, loc=(0, 0))

	def actualizaGraficosVentanaGraficos(self):

		self.tiempoVector.append(self.tiempo.get())
		self.masaVector.append(float(self.masa.get()))

		self.presionBajaVector.append(float(self.presionBaja.get())) 
		self.presionAltaVector.append(float(self.presionAlta.get())) 
		self.tempMuestraVector.append(float(self.tempMuestra.get())) 
		self.caudalMasa1Vector.append(float(self.caudalMasa1.get())) 
		self.caudalMasa2Vector.append(float(self.caudalMasa2.get())) 
		self.caudalMasa3Vector.append(float(self.caudalMasa3.get()))

		self.tempSetVector.append(float(self.tempSet.get()))
		self.presSetVector.append(float(self.presSet.get()))
		self.cau1SetVector.append(float(self.cau1Set.get()))
		self.cau2SetVector.append(float(self.cau2Set.get()))
		self.cau3SetVector.append(float(self.cau3Set.get()))


		self.figMvt = mpl.figure.Figure(figsize=(10,5.4),frameon = True)
		ax = self.figMvt.add_subplot(111)
		ax.set_xlabel("Tiempo [s]")
		ax.set_ylabel("Masa [ug]")
		if(self.rangoCustomX.get() == True):
			ax.set_xlim(self.xmin.get(), self.xmax.get())
		if(self.rangoCustomY.get() == True):
			ax.set_ylim(self.ymin.get(), self.ymax.get())
		ax.grid(b=True)
		ax.plot(np.asarray(self.tiempoVector), np.asarray(self.masaVector))
		self.graficoMasaTiempo = self.draw_figure(self.canvasMasavsTiempo, self.figMvt, loc=(0, 0))

		self.figMvT = mpl.figure.Figure(figsize=(10,5.4), frameon = True)
		ax = self.figMvT.add_subplot(111)
		ax.set_xlabel("Temperatura [°C]")
		ax.set_ylabel("Masa [ug]")
		if(self.rangoCustomX.get() == True):
			ax.set_xlim(self.xmin.get(), self.xmax.get())
		if(self.rangoCustomY.get() == True):
			ax.set_ylim(self.ymin.get(), self.ymax.get())
		ax.grid(b=True)
		ax.plot(np.asarray(self.tempMuestraVector), np.asarray(self.masaVector))
		self.graficoMasaTemp = self.draw_figure(self.canvasMasavsTemper, self.figMvT, loc=(0, 0))

		self.figMvP = mpl.figure.Figure(figsize=(10,5.4), frameon = True)
		ax = self.figMvP.add_subplot(111)
		ax.set_xlabel("Presion [torr]")
		ax.set_ylabel("Masa [ug]")
		if(self.rangoCustomX.get() == True):
			ax.set_xlim(self.xmin.get(), self.xmax.get())
		if(self.rangoCustomY.get() == True):
			ax.set_ylim(self.ymin.get(), self.ymax.get())
		ax.grid(b=True)
		ax.plot(np.asarray(self.presionAltaVector), np.asarray(self.masaVector))
		self.graficoMasaPresion = self.draw_figure(self.canvasMasavsPresio, self.figMvP, loc=(0, 0))

		self.figTvt = mpl.figure.Figure(figsize=(10,5.4), frameon = True)
		ax = self.figTvt.add_subplot(111)
		ax.set_xlabel("Tiempo [s]")
		ax.set_ylabel("Temperatura [°C]")
		if(self.rangoCustomX.get() == True):
			ax.set_xlim(self.xmin.get(), self.xmax.get())
		if(self.rangoCustomY.get() == True):
			ax.set_ylim(self.ymin.get(), self.ymax.get())
		ax.grid(b=True)
		ax.plot(np.asarray(self.tiempoVector), np.asarray(self.tempMuestraVector), label = "Medido")
		ax.plot(np.asarray(self.tiempoVector), np.asarray(self.tempSetVector), label = "Seteado")
		self.graficoTempTiempo = self.draw_figure(self.canvasTempvsTiempo, self.figTvt, loc=(0, 0))

		self.figPvt = mpl.figure.Figure(figsize=(10,5.4), frameon = True)
		ax = self.figPvt.add_subplot(111)
		ax.set_xlabel("Tiempo [s]")
		ax.set_ylabel("Presion [torr]")
		if(self.rangoCustomX.get() == True):
			ax.set_xlim(self.xmin.get(), self.xmax.get())
		if(self.rangoCustomY.get() == True):
			ax.set_ylim(self.ymin.get(), self.ymax.get())
		ax.grid(b=True)
		ax.plot(np.asarray(self.tiempoVector), np.asarray(self.presionAltaVector), label = "Medido")
		ax.plot(np.asarray(self.tiempoVector), np.asarray(self.presSetVector), label = "Seteado")
		self.graficoPresTiempo = self.draw_figure(self.canvasPresvsTiempo, self.figPvt, loc=(0, 0))


		self.figFvt = mpl.figure.Figure(figsize=(10,5.4), frameon = True)
		ax = self.figFvt.add_subplot(111)
		ax.set_xlabel("Tiempo [s]")
		ax.set_ylabel("Caudal [sccm]")
		if(self.rangoCustomX.get() == True):
			ax.set_xlim(self.xmin.get(), self.xmax.get())
		if(self.rangoCustomY.get() == True):
			ax.set_ylim(self.ymin.get(), self.ymax.get())
		ax.grid(b=True)
		ax.plot(np.asarray(self.tiempoVector), np.asarray(self.caudalMasa1Vector), label = "1, Medido")
		ax.plot(np.asarray(self.tiempoVector), np.asarray(self.caudalMasa2Vector), label = "2, Medido")
		ax.plot(np.asarray(self.tiempoVector), np.asarray(self.caudalMasa3Vector), label = "3, Medido")
		ax.plot(np.asarray(self.tiempoVector), np.asarray(self.cau1SetVector), label = "1, Seteado")
		ax.plot(np.asarray(self.tiempoVector), np.asarray(self.cau2SetVector), label = "2, Seteado")
		ax.plot(np.asarray(self.tiempoVector), np.asarray(self.cau3SetVector), label = "3, Seteado")
		self.graficoFlujoTiempo = self.draw_figure(self.canvasFlujvsTiempo, self.figFvt, loc=(0, 0))

	def todoEnCero(self):

		for valvula in range(16):
			cierraValvula(valvula)
		cierraValvula("VB")
		cierraValvula("PCO")
		cierraValvula("PCC")
		#seteaPresion(0)
		seteaTemperaturaHorno(0)
		#seteaTemperaturaBaño(0)
		seteaCaudalMasico(0,1)
		seteaCaudalMasico(0,2)
		seteaCaudalMasico(0,3)

	def condicionSalida(self):
		dicc = {"t": [self.checkboxCondiciont.get()], 
		"T": [self.checkboxCondicionT.get(), self.tempSalida.get()], 
		"p": [self.checkboxCondicionP.get(), self.presSalida.get()], 
		"dp/dt": [self.checkboxCondiciondpdt.get(), self.dpdtSalida.get()], 
		"dT/dt": [self.checkboxCondiciondTdt.get(), self.dTdtSalida.get()],
		"dm/dt": [self.checkboxCondiciondmdt.get(), self.dmdtSalida.get()]}
		return dicc

	def obtengoValoresArbol(self, event):
		item = self.arbolExperimentos.selection()
		self.tempInicial.set(self.arbolExperimentos.item(item)["values"][0])
		self.tempFinal.set(self.arbolExperimentos.item(item)["values"][1])
		self.presionInicial.set(self.arbolExperimentos.item(item)["values"][2])
		self.presionFinal.set(self.arbolExperimentos.item(item)["values"][3])
		self.flujo1Inicial.set(self.arbolExperimentos.item(item)["values"][4])
		self.flujo2Inicial.set(self.arbolExperimentos.item(item)["values"][5])
		self.flujo3Inicial.set(self.arbolExperimentos.item(item)["values"][6])
		self.flujo1Final.set(self.arbolExperimentos.item(item)["values"][7])
		self.flujo2Final.set(self.arbolExperimentos.item(item)["values"][8])
		self.flujo3Final.set(self.arbolExperimentos.item(item)["values"][9])
		self.tiempoTotal.set(self.arbolExperimentos.item(item)["values"][10])
		self.tiempoPaso.set(self.arbolExperimentos.item(item)["values"][11])

		self.checkboxFlujo1.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].checkboxFlujo1)
		self.checkboxFlujo2.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].checkboxFlujo2)
		self.checkboxFlujo3.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].checkboxFlujo3)
		self.checkboxFlujoHorno.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].checkboxFlujoHorno)
		self.checkboxFlujoVenteo.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].checkboxFlujoVenteo)
		self.checkboxFlujoVenteoHorno.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].checkboxFlujoVenteoHorno)

		self.botonCheckboxFlujo1()
		self.botonCheckboxFlujo2()
		self.botonCheckboxFlujo3()
		self.botonCheckboxCondiciondmdt()
		self.botonCheckboxCondiciondpdt()
		self.botonCheckboxCondiciont()
		self.botonCheckboxCondiciondTdt()
		self.botonCheckboxCondicionT()
		self.botonCheckboxCondicionP()

		self.checkboxCondiciont.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].condicion_salida["t"][0])
		self.checkboxCondicionT.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].condicion_salida["T"][0])
		self.tempSalida.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].condicion_salida["T"][1])
		self.checkboxCondicionP.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].condicion_salida["p"][0])
		self.presSalida.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].condicion_salida["p"][1])
		self.checkboxCondiciondpdt.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].condicion_salida["dp/dt"][0])
		self.checkboxCondiciondTdt.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].condicion_salida["dT/dt"][0])
		self.checkboxCondiciondmdt.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].condicion_salida["dm/dt"][0])
		self.dpdtSalida.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].condicion_salida["dp/dt"][1])
		self.dTdtSalida.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].condicion_salida["dT/dt"][1])
		self.dmdtSalida.set(self.experimentoVariable.expLista[int(self.arbolExperimentos.item(item)["text"])].condicion_salida["dm/dt"][1])

	def armaExperimentoLog(self):
		now = datetime.datetime.now()
		fname = self.filenameCarpeta.get()+"/"
		fnameExp = fname + "ExperimentoLog.txt"

		os.makedirs(os.path.dirname(fname), exist_ok=True)
		with open(fnameExp, "w") as f:
			f.write(''.join(['''		Registro de experimento - Medición termogravimétrica

		Información general:
		
		Autor:''', str(self.descripcion.get()), '''
		Fecha: ''', str(now.year),"/",str(now.month),"/",str(now.day), '''
		Hora: ''' ,str(now.hour),"h",str(now.minute),"m" , '''
		Muestra: ''',self.nombreArchivo.get(),'''
		Descripción: ''',self.descripcion.get(),'''
		Número de subexperimentos: ''',str(len(self.experimentoVariable.expLista)),'''
		
		Variables de control:
		
		Pr: ''', str(self.alphaVar.get()),'''
		In: ''', str(self.gammaVar.get()),'''
		De: ''',str(self.betaVar.get()),'''
		
		Maximo tiempo de apertura: ''',str(self.tmaxVar.get()),'''
		Apertura mínima de control: ''',str(self.deltaApMinVar.get()),'''
		Derivada máxima de subida/bajada: ''',str(self.dpmaxVar.get()),'''
		
		Subexperimentos:
				''']))
			i=0
			for subExp in self.experimentoVariable.expLista:
				i+=1
				f.write("N°:"+str(i)+"\n")

				f.write("	Tiempo total: "+str(subExp.tiempoTotal)+"\n")
				f.write("	Paso de tiempo: "+str(subExp.tiempoPaso)+"\n")
				f.write("	Temperatura inicial: "+str(subExp.tempInicial) +"\n")
				f.write("	Temperatura final: "+str(subExp.tempFinal)+"\n")
				f.write("	Presión inicial: "+str(subExp.presionInicial)+"\n")
				f.write("	Presión final: "+str(subExp.presionFinal) +"\n")
				f.write("	Flujo He inicial: "+str(subExp.flujoInicial1)+"\n")
				f.write("	Flujo H inicial: "+str(subExp.flujoInicial2)+"\n")
				f.write("	Flujo N inicial: "+str(subExp.flujoInicial3)+"\n")
				f.write("	Flujo He final "+str(subExp.flujoFinal1)+"\n")
				f.write("	Flujo H final: "+str(subExp.flujoFinal2)+"\n")
				f.write("	Flujo N final: "+str(subExp.flujoFinal3)+"\n")
				f.write("	Válvula Flujo 1 "+str(subExp.checkboxFlujo1)+"\n")
				f.write("	Válvula Flujo 2 "+str(subExp.checkboxFlujo2)+"\n")
				f.write("	Válvula Flujo 3 "+str(subExp.checkboxFlujo3)+"\n")
				f.write("	Válvula  G-V"+str(subExp.checkboxFlujoVenteo)+"\n")
				f.write("	Válvula  G-H"+str(subExp.checkboxFlujoHorno)+"\n")
				f.write("	Válvula  H-V"+str(subExp.checkboxFlujoVenteoHorno)+"\n")
				f.write("	Diccionario de condicion de salida:  "+str(subExp.condicion_salida) + "\n\n")

class masterThread:
	def __init__(self, master):
		print("holu\n")

		self.master = master

		self.queue = queue.Queue()
		self.queuePressure = queue.Queue()

		self.gui = GUI(master, self.queue, self.queuePressure, self.kill)

		self.corriendo = 1

		self.chequeoPeriodico()

		self.thread1 = threading.Thread(target=self.chequeaSiEjecuta)
		self.thread1.start()

		self.thread2 = threading.Thread(target = self.loopPresionPID)
		self.thread2.start()

	def chequeoPeriodico(self):

		self.gui.procesoLlegando()

		if(self.corriendo == 0):
			import sys
			sys.exit(1)
		self.master.after(200, self.chequeoPeriodico)

	def kill(self):
		#self.gui.guardaGraficosyArchivos()
		if self.gui.experimentoVariable.correExperimento:
			self.gui.experimentoVariable.kill = 1
			self.gui.guardaGraficosyArchivos()
		self.gui.todoEnCero()
		self.corriendo = 0

	def chequeaSiEjecuta(self):
		while(self.corriendo):
			if(self.gui.experimentoVariable.correExperimento==1):

				self.gui.experimentoVariable.ejecuta()
				if(self.gui.experimentoVariable.kill == 0):
					self.gui.experimentoVariable.correExperimento=0
					self.gui.guardaGraficosyArchivos()
					self.gui.todoEnCero()

			if(self.gui.experimentoVariable.correExperimentoPresion==1):

				self.gui.experimentoVariable.ejecutaPresion(self.gui.dpdtSalida.get())
				self.gui.experimentoVariable.correExperimentoPresion=0
				self.gui.todoEnCero()
				self.gui.guardaGraficosyArchivos()

			if(self.gui.experimentoVariable.definePosicion == 1):

				self.gui.experimentoVariable.definedNdp()
				self.gui.definePosicion = 0
				self.gui.todoEnCero()
				self.gui.guardaGraficosyArchivos()

			if(self.gui.experimentoVariable.buscaPosicion == 1):

				self.gui.experimentoVariable.buscaPosicionValvula()
				self.gui.buscaPosicion = 0
				self.gui.todoEnCero()
				self.gui.guardaGraficosyArchivos()

			time.sleep(0.1)

	def loopPresionPID(self):

		while(self.corriendo):
			if(self.queuePressure.qsize()):
				
				try:
					vector_presion = self.queuePressure.get(0)

					if(len(vector_presion)==2):

						if vector_presion[0] == 'open':
							print("Manual open" + str(vector_presion[1]) + "s")
							abreValvula('PCO')
							time.sleep(vector_presion[1])
							cierraValvula('PCO')
						elif vector_presion[0] == 'close':
							print("Manual close" + str(vector_presion[1]) + "s")
							abreValvula('PCC')
							time.sleep(vector_presion[1])
							cierraValvula('PCC')

					if(len(vector_presion) == 4):

						print("queue right size ", self.gui.controlo.get())
						if self.gui.controlo.get() == 1: 

							if(self.corriendo==0):
								break
							print("controlo!")
							vector_presion = self.queuePressure.get()

							presionSp = vector_presion[0]
							presion = vector_presion[1]
							derivada = vector_presion[2]
							flujo = vector_presion[3]
							tmax = self.gui.tmaxVar.get()
							dpmax = self.gui.dpmaxVar.get()
							deltaApMin = self.gui.deltaApMinVar.get()

							print(dpmax)

							if (abs(derivada) < 100):

								deltaApertura = self.gui.alphaVar.get()*(presion - presionSp) + self.gui.betaVar.get()*derivada
	
								print("El delta de apertura es: " + str(deltaApertura))

								if(deltaApertura > tmax):
									if (derivada <= -dpmax):
										deltaApertura = 0
									else:
										deltaApertura = tmax

								if(deltaApertura < -tmax):
									if (derivada >= dpmax):
										deltaApertura = 0
									else:
										deltaApertura = -tmax

								if(abs(deltaApertura) > deltaApMin):
	
									if (deltaApertura>0):
										print("Auto open" + str(deltaApertura) + "s")
										abreValvula('PCO')
										time.sleep(deltaApertura)
										cierraValvula('PCO')
	
									if (deltaApertura<0):
										print("Auto close" + str(deltaApertura) + "s")
										abreValvula('PCC')
										time.sleep(-deltaApertura)
										cierraValvula('PCC')
								else:
									print("no vale la pena por ese tiempito, o estamos en derivada maxima")


				except queue.Empty:
					pass
			
			time.sleep(0.5)	

def mainFunction():

	if(estoy_balanza):
		abreComunicacion()
		pass

	rand = random.Random()
	root = Tk()

	client = masterThread(root)



	root.mainloop()

mainFunction()
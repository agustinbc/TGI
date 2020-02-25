""" -----------------------------------------------------------------------------------------
#								  Programa Termobalanza 									#
#								  Librería de funciones										#
#					-------------------------------------------------						#
#								Creado por Agustín Bernardo									#
#							   email: bagustin.sfe@gmail.com								#
#							   		0800 - 777 - 24772										#
#								       Versión: 0.1											#
#									  Fecha: 13/2/2019										#
#					-------------------------------------------------						#
#									    Changelog:											#
-------------------------------------------------------------------------------------------"""




from PyDAQmx import *
import numpy
import serial
from ctypes import *
import time
from math import log10, floor

def func_exp(x, a, b, c):
    return a * np.exp(-b * (x)) + c

def round_sig(x, sig=2):
	if x==0:
		return x
	return round(x, sig-int(floor(log10(abs(x))))-1)

masa_ficticia = 0.0


decimalNumberPressure = 6
decimalNumberMass = 6
decimalNumberTemp = 4
decimalNumberFlow = 4


valvulas = dict()
calibraciones = dict()

ser = serial.Serial()


valvulas = {
		#DEV, PORT, PIN 
	0 : 	[1,0,0], 
	1 : 	[1,0,1],
	2 : 	[1,0,2],
	3 : 	[1,0,3],
	4 : 	[1,0,4],
	5 : 	[1,0,5],
	6 : 	[1,0,6],
	7 : 	[1,0,7],
	8 : 	[1,1,0],
	9 : 	[1,1,1],
	13: 	[1,1,2],
	14: 	[1,1,3],
	15: 	[1,1,4],
	10: 	[1,1,5],
	11: 	[1,1,6],
	12: 	[1,1,7],
	"VB": 	[1,2,0],
	"BC":	[1,2,1],
	"PCO":	[1,2,2],
	"PCC":	[1,2,3],
	}

calibraciones = {
			#MODIFICAR CON LA CALIBRACIÓN CORRESPONDIENTE
	"pendientePL" 	: 100.,
	"pendientePH" 	: 9186.1728515625,
	"pendienteTM" 	: 280.8718566894531,
	"pendienteRTD"	: 1.,#COMPLETAR
	
	"pendienteFurn" : 220.0,#COMPLETAR
	"AFurn" 		: -0.0002,
	"BFurn"			: 1.1342,
	"pendienteMFC" 	: 100.0,#COMPLETAR
	"pendienteMfcO" : 0.01,#COMPLETAR
	"pendienteBath" : 0.01,#COMPLETAR
	"offsetPL" 		: 0.,
	"offsetPH" 		: 0.,
	"offsetTM" 		: -84.65931701660156,
	"offsetRTD"		: 0.,#COMPLETAR
	"offsetFurn"	: 0.,#COMPLETAR
	"offsetMFC" 	: 0.,#COMPLETAR
	"offsetMfcO"	: 0.,#COMPLETAR
	"offsetBath"	: 0.,#COMPLETAR	
}



ser.port = 'COM1'

ser.timeout = 3

def convierteTauPresion(tau, flujo):
	return (flujo/50)**(0.937) *1.4* tau + 740

def conviertePresionTau(presion, flujo):
	return (presion - 740)/1.4 * (50/flujo)**(0.937)

def conviertePresionPosicion(presion, flujo):
	if (presion*(flujo/50)**(0.937)>1400):
		return 1/(0.0012*(((presion - 740)/(flujo/50)**(.937))**(1/2))) - 7.65
	else:
		return 0



def sampleOptimos(dt):
	#acá iría el valor medido de los samples, bah, cuánto toman, y el tiempo, algo como "return dt*15+5", nu se
	pass

def midePresionBaja(samples):
	task = Task()
	read = int32()
	data = numpy.zeros((samples,), dtype=numpy.float64)

	task.CreateAIVoltageChan("Dev1/ai0","",DAQmx_Val_Cfg_Default,-10.0,10.0,DAQmx_Val_Volts,None) #DEVICE
	task.CfgSampClkTiming("",10000.0,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,samples)

	task.StartTask()

	task.ReadAnalogF64(-1,1000.0,DAQmx_Val_GroupByChannel,data,samples,byref(read),None)

	task.StopTask()
	task.ClearTask()

	return round_sig(data.mean()*calibraciones["pendientePL"]+calibraciones["offsetPL"],decimalNumberPressure)

def midePresionAlta(samples):
	task = Task()
	read = int32()
	data = numpy.zeros((samples,), dtype=numpy.float64)

	task.CreateAIVoltageChan("Dev1/ai1","",DAQmx_Val_Cfg_Default,-10.0,10.0,DAQmx_Val_Volts,None) #DEVICE
	task.CfgSampClkTiming("",10000.0,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,samples)

	task.StartTask()

	task.ReadAnalogF64(-1,1000.0,DAQmx_Val_GroupByChannel,data,samples,byref(read),None)

	task.StopTask()
	task.ClearTask()
	return round_sig(data.mean()*calibraciones["pendientePH"]+calibraciones["offsetPH"],decimalNumberPressure)

def mideTemperaturaMuestra(samples):
	
	task = Task()
	read = int32()
	data = numpy.zeros((samples,), dtype=numpy.float64)

	task.CreateAIVoltageChan("Dev1/ai2","",DAQmx_Val_Cfg_Default,-10.0,10.0,DAQmx_Val_Volts,None)
	task.CfgSampClkTiming("",10000.0,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,samples)

	task.StartTask()

	task.ReadAnalogF64(-1,1000.0,DAQmx_Val_GroupByChannel,data,samples,byref(read),None)

	task.StopTask()
	task.ClearTask()

	return round_sig(data.mean()*calibraciones["pendienteTM"]+calibraciones["offsetTM"],decimalNumberTemp)

def mideTemperaturaTubo(samples, tubo):
	
	task = Task()
	read = int32()
	data = numpy.zeros((samples,), dtype=numpy.float64)

	task.CreateAIVoltageChan("Dev1/ai"+str(tubo+1),"",DAQmx_Val_Cfg_Default,-10.0,10.0,DAQmx_Val_Volts,None)
	task.CfgSampClkTiming("",10000.0,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,samples)

	task.StartTask()

	task.ReadAnalogF64(-1,1000.0,DAQmx_Val_GroupByChannel,data,samples,byref(read),None)

	task.StopTask()
	task.ClearTask()

	return round_sig(data.mean()*calibraciones["pendienteRTD"]+calibraciones["offsetRTD"],decimalNumberTemp)

def mideCaudalMasico(samples, cond):
	
	task = Task()
	read = int32()
	data = numpy.zeros((samples,), dtype=numpy.float64)

	task.CreateAIVoltageChan("Dev1/ai"+str(cond+4),"",DAQmx_Val_Cfg_Default,-10.0,10.0,DAQmx_Val_Volts,None)
	task.CfgSampClkTiming("",10000.0,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,samples)

	task.StartTask()

	task.ReadAnalogF64(-1,1000.0,DAQmx_Val_GroupByChannel,data,samples,byref(read),None)

	task.StopTask()
	task.ClearTask()

	return round_sig(data.mean()*calibraciones["pendienteMFC"]+calibraciones["offsetMFC"],decimalNumberFlow)

def seteaCaudalMasico(caudal, cond):
	task = Task()

	voltOut = caudal*calibraciones["pendienteMfcO"]+calibraciones["offsetMfcO"]
	
	task.CreateAOVoltageChan("/Dev2/ao"+str(cond-1),"",0,5.0,DAQmx_Val_Volts,None)
	task.StartTask()
	
	task.WriteAnalogScalarF64(1,10.0,voltOut,None)
	
	task.StopTask()
	task.ClearTask()

def seteaTemperaturaHorno(temp):
	task = Task()

	voltOut = 1/calibraciones["pendienteFurn"] * (temp**2*calibraciones["AFurn"]+temp*calibraciones["BFurn"]+calibraciones["offsetFurn"])
	
	task.CreateAOVoltageChan("/Dev1/ao1","",0.,5.0,DAQmx_Val_Volts,None)
	task.StartTask()
	
	task.WriteAnalogScalarF64(1,10.0,voltOut,None)
	
	task.StopTask()
	task.ClearTask()

def seteaTemperaturaBaño(temp):
	task = Task()
	voltOut = temp*calibraciones["pendienteBath"]+calibraciones["offsetBath"]
	
	task.CreateAOVoltageChan("/Dev1/ao0","",0.,5.,DAQmx_Val_Volts,None)
	task.StartTask()
	
	task.WriteAnalogScalarF64(1,10.0,voltOut,None)
	
	task.StopTask()
	task.ClearTask()

def abreValvula(nombre):
	
	data = numpy.array([0,0,0,0,0,0,0,0], dtype=numpy.uint8)
	read = int32()
	bytesPerSamp = int32()

	deviceNumber =	str(valvulas[nombre][0])
	portNumber 	=   str(valvulas[nombre][1])
	pinNumber =	 	valvulas[nombre][2]


	lectura = Task()

	lectura.CreateDOChan("Dev"+deviceNumber+"/port"+portNumber+"/line0:7","",DAQmx_Val_ChanForAllLines)
	lectura.ReadDigitalLines(1,10.0,DAQmx_Val_GroupByChannel,data,8,byref(read),byref(bytesPerSamp),None)

	print(data, deviceNumber, portNumber, pinNumber, "abrir")

	data[pinNumber] = 1

	lectura.WriteDigitalLines(1,1,10.0,DAQmx_Val_GroupByChannel,data,None,None)
	lectura.StopTask()

def cierraValvula(nombre):

	data = numpy.array([0,0,0,0,0,0,0,0], dtype=numpy.uint8)
	read = int32()
	bytesPerSamp = int32()

	deviceNumber =	str(valvulas[nombre][0])
	portNumber 	=   str(valvulas[nombre][1])
	pinNumber =	 	valvulas[nombre][2]


	lectura = Task()

	lectura.CreateDOChan("Dev"+deviceNumber+"/port"+portNumber+"/line0:7","",DAQmx_Val_ChanForAllLines)
	lectura.ReadDigitalLines(1,10.0,DAQmx_Val_GroupByChannel,data,8,byref(read),byref(bytesPerSamp),None)

	print(data, deviceNumber, portNumber, pinNumber, "cerrar")

	data[pinNumber] = 0

	lectura.WriteDigitalLines(1,1,10.0,DAQmx_Val_GroupByChannel,data,None,None)
	lectura.StopTask()

#def calibraBalanza():
def mideVectorValvulas():

	data1 = numpy.array([0,0,0,0,0,0,0,0], dtype=numpy.uint8)
	data2 = numpy.array([0,0,0,0,0,0,0,0], dtype=numpy.uint8)
	read = int32()
	bytesPerSamp = int32()

	lectura1 = Task()
	lectura2 = Task()

	lectura1.CreateDOChan("Dev1/port0/line0:7","",DAQmx_Val_ChanForAllLines)
	lectura1.StartTask()
	lectura1.ReadDigitalLines(1,10.0,DAQmx_Val_GroupByChannel,data1,8,byref(read),byref(bytesPerSamp),None)
	lectura1.StopTask()

	lectura2.CreateDOChan("Dev1/port1/line0:7","",DAQmx_Val_ChanForAllLines)
	lectura2.StartTask()
	lectura2.ReadDigitalLines(1,10.0,DAQmx_Val_GroupByChannel,data2,8,byref(read),byref(bytesPerSamp),None)
	lectura2.StopTask()

	#print(data1.tolist(),data2.tolist()[:2],data2.tolist()[4:7],data2.tolist()[1:4])

	return  data1.tolist()+data2.tolist()[0:2] +data2.tolist()[5:8]+data2.tolist()[2:5]

#def taraBalanza():
def abreComunicacion():
	ser.open()

def mideBalanza():
	ser.write(b'p')
	string = ser.readline()
	splitted = string.split()
	return splitted[0].decode()/1000.0 + masa_ficticia

def cierraComunicacion():
	ser.close()

def seteaElZero(masa):
	masa_ficticia = masa
	ser.write(b'z')
	string = ser.readline()
	if(string != None):
		print("seteado")

def panico():

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
#abreComunicacion()






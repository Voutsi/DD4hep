#
#
import os, time, DDG4
from DDG4 import OutputLevel as Output
from SystemOfUnits import *
#
#
"""

   DD4hep simulation example setup using the python configuration

   @author  M.Frank
   @version 1.0

"""
def run():
  kernel = DDG4.Kernel()
  lcdd = kernel.lcdd()
  install_dir = os.environ['DD4hepINSTALL']
  kernel.loadGeometry("file:"+install_dir+"/DDDetectors/compact/SiD_Markus.xml")
  DDG4.importConstants(lcdd)
  DDG4.Core.setPrintLevel(Output.WARNING)

  geant4 = DDG4.Geant4(kernel,tracker='Geant4TrackerWeightedAction')
  geant4.printDetectors()
  # Configure UI
  geant4.setupCshUI()

  # Configure G4 magnetic field tracking
  field = geant4.addConfig('Geant4FieldTrackingSetupAction/MagFieldTrackingSetup')
  field.stepper            = "HelixGeant4Runge"
  field.equation           = "Mag_UsualEqRhs"
  field.eps_min            = 5e-05 * mm
  field.eps_max            = 0.001 * mm
  field.min_chord_step     = 0.01 * mm
  field.delta_chord        = 0.25 * mm
  field.delta_intersection = 1e-05 * mm
  field.delta_one_step     = 0.001 * mm
  print '+++++> ',field.name,'-> stepper  = ',field.stepper
  print '+++++> ',field.name,'-> equation = ',field.equation
  print '+++++> ',field.name,'-> eps_min  = ',field.eps_min
  print '+++++> ',field.name,'-> eps_max  = ',field.eps_max
  print '+++++> ',field.name,'-> delta_one_step = ',field.delta_one_step

  # Setup random generator
  rndm = DDG4.Action(kernel,'Geant4Random/Random')
  rndm.Seed = 987654321
  rndm.initialize()

  # Configure Run actions
  run1 = DDG4.RunAction(kernel,'Geant4TestRunAction/RunInit')
  run1.Property_int    = 12345
  run1.Property_double = -5e15*keV
  run1.Property_string = 'Startrun: Hello_2'
  print run1.Property_string, run1.Property_double, run1.Property_int
  run1.enableUI()
  kernel.registerGlobalAction(run1)
  kernel.runAction().adopt(run1)

  # Configure Event actions
  prt = DDG4.EventAction(kernel,'Geant4ParticlePrint/ParticlePrint')
  prt.OutputLevel = Output.DEBUG
  prt.OutputType  = 3 # Print both: table and tree
  kernel.eventAction().adopt(prt)

  # Configure Event actions
  prt = DDG4.EventAction(kernel,'Geant4SurfaceTest/SurfaceTest')
  prt.OutputLevel = Output.INFO
  kernel.eventAction().adopt(prt)

  # Configure I/O
  evt_lcio = geant4.setupLCIOOutput('LcioOutput','CLICSiD_'+time.strftime('%Y-%m-%d_%H-%M'))
  evt_lcio.OutputLevel = Output.DEBUG

  #evt_root = geant4.setupROOTOutput('RootOutput','CLICSiD_'+time.strftime('%Y-%m-%d_%H-%M'))
  #generator_output_level = Output.INFO
  
  gen = DDG4.GeneratorAction(kernel,"Geant4GeneratorActionInit/GenerationInit")
  kernel.generatorAction().adopt(gen)

  #VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
  """
  Generation of isotrope tracks of a given multiplicity with overlay:
  """
  # First particle generator: pi+
  gen = DDG4.GeneratorAction(kernel,"Geant4IsotropeGenerator/IsotropPi+");
  gen.Particle = 'pi+'
  gen.Energy = 100 * GeV
  gen.Multiplicity = 2
  gen.Mask = 1
  gen.OutputLevel = Output.DEBUG
  gen.PhiMin = 0
  gen.PhiMax = 0
  gen.ThetaMin = 1.61
  gen.ThetaMax = 1.61

  kernel.generatorAction().adopt(gen)
  # Install vertex smearing for this interaction
  gen = DDG4.GeneratorAction(kernel,"Geant4InteractionVertexSmear/SmearPi+");
  gen.Mask = 1
  gen.Offset = (20*mm, 10*mm, 10*mm, 0*ns)
  gen.Sigma = (4*mm, 1*mm, 1*mm, 0*ns)
  kernel.generatorAction().adopt(gen)
  """
  # Second particle generator: e-
  gen = DDG4.GeneratorAction(kernel,"Geant4IsotropeGenerator/IsotropE-");
  gen.Particle = 'e-'
  gen.Energy = 25 * GeV
  gen.Multiplicity = 3
  gen.Mask = 2
  gen.OutputLevel = Output.DEBUG
  kernel.generatorAction().adopt(gen)
  # Install vertex smearing for this interaction
  gen = DDG4.GeneratorAction(kernel,"Geant4InteractionVertexSmear/SmearE-");
  gen.Mask = 2
  gen.Offset = (-20*mm, -10*mm, -10*mm, 0*ns)
  gen.Sigma = (12*mm, 8*mm, 8*mm, 0*ns)
  kernel.generatorAction().adopt(gen)
  #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  """
  # Merge all existing interaction records
  gen = DDG4.GeneratorAction(kernel,"Geant4InteractionMerger/InteractionMerger")
  gen.OutputLevel = 4 #generator_output_level
  gen.enableUI()
  kernel.generatorAction().adopt(gen)

  # Finally generate Geant4 primaries
  gen = DDG4.GeneratorAction(kernel,"Geant4PrimaryHandler/PrimaryHandler")
  gen.OutputLevel = Output.DEBUG #generator_output_level
  gen.enableUI()
  kernel.generatorAction().adopt(gen)

  # And handle the simulation particles.
  part = DDG4.GeneratorAction(kernel,"Geant4ParticleHandler/ParticleHandler")
  kernel.generatorAction().adopt(part)
  #part.SaveProcesses = ['conv','Decay']
  part.SaveProcesses = ['Decay']
  part.MinimalKineticEnergy = 100*MeV
  part.OutputLevel = Output.DEBUG # generator_output_level
  part.enableUI()
  user = DDG4.Action(kernel,"Geant4TCUserParticleHandler/UserParticleHandler")
  user.TrackingVolume_Zmax = DDG4.EcalEndcap_zmin
  user.TrackingVolume_Rmax = DDG4.EcalBarrel_rmin
  user.enableUI()
  part.adopt(user)

  # Setup global filters fur use in sensntive detectors
  f1 = DDG4.Filter(kernel,'GeantinoRejectFilter/GeantinoRejector')
  kernel.registerGlobalFilter(f1)

  # First the tracking detectors
  seq,act = geant4.setupTracker('SiVertexBarrel')
  act.OutputLevel = Output.ERROR
  act.CollectSingleDeposits = False
  seq,act = geant4.setupTracker('SiVertexEndcap')
  act.OutputLevel = Output.ERROR
  act.CollectSingleDeposits = False

  #seq,act = geant4.setupTracker('SiTrackerBarrel')
  #seq,act = geant4.setupTracker('SiTrackerEndcap')
  #seq,act = geant4.setupTracker('SiTrackerForward')
  # Now the calorimeters
  #seq,act = geant4.setupCalorimeter('EcalBarrel')
  #seq,act = geant4.setupCalorimeter('EcalEndcap')
  #seq,act = geant4.setupCalorimeter('HcalBarrel')
  #seq,act = geant4.setupCalorimeter('HcalEndcap')
  #seq,act = geant4.setupCalorimeter('HcalPlug')
  #seq,act = geant4.setupCalorimeter('MuonBarrel')
  #seq,act = geant4.setupCalorimeter('MuonEndcap')
  #seq,act = geant4.setupCalorimeter('LumiCal')
  #seq,act = geant4.setupCalorimeter('BeamCal')

  # Now build the physics list:
  phys = geant4.setupPhysics('QGSP_BERT')
  phys.dump()

  kernel.configure()
  kernel.initialize()

  #DDG4.setPrintLevel(Output.DEBUG)
  kernel.run()
  kernel.terminate()

if __name__ == "__main__":
  run()
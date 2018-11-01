from optostim.models.datamodels.stimulus_point import StimulusPoint

point0 = StimulusPoint(location=(10, 15), frame=0, index=0)
point1 = StimulusPoint(location=(20, 40), frame=0, index=1)
point2 = StimulusPoint(location=(55, 60), frame=0, index=2)
point3 = StimulusPoint(location=(15, 10), frame=0, index=3)

test_points = [point0, point1, point2, point3]
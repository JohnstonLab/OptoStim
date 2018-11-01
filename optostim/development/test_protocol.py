import random

from optostim.models.datamodels.protocol_element import ProtocolElement
from optostim.models.datamodels.selected_stimulus_point import SelectedStimulusPoint
from stimulus_points import test_points

pe_0 = ProtocolElement(selected_stimulus_points=[SelectedStimulusPoint(stimulus_point=test_points[0],
                                                                       pattern=SelectedStimulusPoint.Pattern.NORMAL)])
pe_1 = ProtocolElement(selected_stimulus_points=[SelectedStimulusPoint(stimulus_point=test_points[1],
                                                                       pattern=SelectedStimulusPoint.Pattern.INCREMENTBYONE)])
pe_2 = ProtocolElement(selected_stimulus_points=[SelectedStimulusPoint(stimulus_point=test_points[2],
                                                                       pattern=SelectedStimulusPoint.Pattern.RANDOM)])
pe_3 = ProtocolElement(selected_stimulus_points=[SelectedStimulusPoint(stimulus_point=test_points[3],
                                                                       pattern=SelectedStimulusPoint.Pattern.NORMAL),])

protocol_sequence = [pe_0, pe_1, pe_2, pe_3]


loop_count = 5


def generate_one_program_loop(protocol_element):
    points_to_add = []
    deferred_points_to_be_random = []

    for point in protocol_sequence[i].stimulus_points:

        # point_to_add = point.stimulus_point

        if point.pattern == SelectedStimulusPoint.Pattern.INCREMENTBYONE:
            point_to_add = test_points[point.index() + 1]
            points_to_add.append(SelectedStimulusPoint(stimulus_point=point_to_add, pattern=point.pattern))

        elif point.pattern == SelectedStimulusPoint.Pattern.RANDOM:
            deferred_points_to_be_random.append(point)
        else:
            points_to_add.append(point)

    available_test_points = [p for p in test_points
                             if not any(selected_point.index == p.index for selected_point in points_to_add)]

    random_points = []

    for point in deferred_points_to_be_random:
        random_point_to_add = random.choice(available_test_points)
        random_points.append(random_point_to_add)
        available_test_points.remove(random_point_to_add)

    new_sequence = protocol_sequence
    new_sequence.stimulus_points = sorted(points_to_add + random_points, key=lambda x: x.stimulus_point.index)

    program.append(new_sequence)


def new_protocol_element_from_previous(protocol_element):

    points_to_add = []
    random_count = 0

    for point in protocol_element.stimulus_points:

        if point.pattern == SelectedStimulusPoint.Pattern.INCREMENTBYONE:
            point_to_add = test_points[(point.index() + 1) % len(test_points)]
            points_to_add.append(SelectedStimulusPoint(stimulus_point=point_to_add, pattern=point.pattern))
        elif point.pattern == SelectedStimulusPoint.Pattern.RANDOM:
            random_count += 1
        else:
            points_to_add.append(point)

        available_test_points = [p for p in test_points
                                 if not any(selected_point.index == p.index for selected_point in points_to_add)]

        for deferred_point in range(0, random_count):
            random_point_to_add = random.choice(available_test_points)
            points_to_add.append(SelectedStimulusPoint(stimulus_point=random_point_to_add,
                                                       pattern=SelectedStimulusPoint.Pattern.RANDOM))
            available_test_points.remove(random_point_to_add)

    new_element = ProtocolElement()
    new_element.stimulus_points = points_to_add
    new_element.laser = protocol_element.laser
    new_element.pmt = protocol_element.pmt
    new_element.sync = protocol_element.sync
    new_element.wait = protocol_element.wait
    new_element.duration = protocol_element.duration

    return new_element


def create_new_protocol_sequence(previous_protocol_sequence):
    new_protocol_sequence = []

    for protocol_element in previous_protocol_sequence:
        new_protocol_sequence.append(new_protocol_element_from_previous(protocol_element))

    return new_protocol_sequence


program = [protocol_sequence]

for i in range(1, loop_count):

    print('----------loop {}-------------'.format(i))

    new_protocol_sequence = create_new_protocol_sequence(program[i-1])
    program.append(new_protocol_sequence)

True

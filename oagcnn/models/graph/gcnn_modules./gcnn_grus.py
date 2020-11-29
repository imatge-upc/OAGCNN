from .convGRU_cell import ConvGRUCell
import torch.nn as nn
import torch


class GRUGCNN(nn.Module):

    def __init__(self, input_channels):
        super(GRUGCNN, self).__init__()
        self.aggregation_op = self._max_op
        self.aggregation_func = nn.Conv2d(input_channels, input_channels, kernel_size=3, padding=1, bias=False)
        self.self_loop_func = nn.Conv2d(input_channels, input_channels, kernel_size=3, padding=1, bias=False)
        self.update_op = self._cat_op
        self.update_func = nn.Conv2d(input_channels*2, input_channels, kernel_size=3, padding=1, bias=False)

        self.state_update = ConvGRUCell(input_channels, input_channels, 0, 3)

    def _max_op(self, neighbour_states):
        # Neighbour states: LIST (NUM_NODES-1) EACH: (NUM_CHANNELS, H, W)
        # Stack: (NUM_NODES -1, NUM_CHANNELS, H, W)
        # Mean: (1, NUM_CHANNELS, H, W)
        return torch.max(torch.stack(neighbour_states, dim=0), dim=0)

    def _cat_op(self, neighbour_states, self_state):
        return torch.cat((neighbour_states, self_state), dim=0)

    def forward(self, neighbour_states, self_state):

        if not neighbour_states:
            intra = self.self_loop_func(self_state)

            return self.update_func(intra, self_state)

        inter = self.aggregation_op(neighbour_states)
        inter = self.aggregation_func(inter)

        intra = self.self_loop_func(self_state)
        inter_intra = self.update_op(inter, intra)

        inter_intra = self.update_func(inter_intra)

        new_state = self.update_func(inter_intra.unsqueeze(0), self_state.unsqueeze(0))

        return new_state
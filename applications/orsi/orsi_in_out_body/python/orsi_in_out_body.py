# SPDX-FileCopyrightText: Copyright (c) 2022-2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os

from holoscan.core import Application
from holoscan.logger import LogLevel, set_log_level
from holoscan.operators import InferenceOp, VideoStreamReplayerOp
from holoscan.resources import UnboundedAllocator

from holohub.orsi_format_converter import OrsiFormatConverterOp
from holohub.orsi_segmentation_preprocessor import OrsiSegmentationPreprocessorOp
from holohub.orsi_visualizer import OrsiVisualizationOp

# from holoscan.videomaster import VideoMasterSourceOp


class OrsiInOutBodyApp(Application):
    def __init__(self):
        super().__init__()
        self.name = "OrsiInOutBodyApp"
        self.data_path = os.environ.get("HOLOSCAN_DATA_PATH", "../data/orsi")

    def compose(self):
        allocator = UnboundedAllocator(self, name="allocator")
        # Built-in Holoscan operators
        source = VideoStreamReplayerOp(
            self,
            name="replayer",
            directory=self.data_path,
            **self.kwargs("replayer"),
        )
        multi_ai_inference = InferenceOp(
            self,
            name="multiai_inference",
            allocator=allocator,
            model_path_map={"anonymization": self.data_path + "/models/anonymization_model.onnx"},
            **self.kwargs("multiai_inference"),
        )
        # Orsi operators
        anonymization_preprocessor = OrsiSegmentationPreprocessorOp(
            self,
            name="anonymization_preprocessor",
            allocator=allocator,
            **self.kwargs("anonymization_preprocessor"),
        )
        format_converter_anonymization = OrsiFormatConverterOp(
            self,
            name="format_converter",
            allocator=allocator,
            **self.kwargs("format_converter_anonymization"),
        )
        orsi_visualizer = OrsiVisualizationOp(
            self,
            name="orsi_visualizer",
            **self.kwargs("orsi_visualizer"),
        )
        self.add_flow(source, orsi_visualizer, {("", "receivers")})
        self.add_flow(source, format_converter_anonymization)
        self.add_flow(format_converter_anonymization, anonymization_preprocessor)
        self.add_flow(anonymization_preprocessor, multi_ai_inference, {("", "receivers")})
        self.add_flow(multi_ai_inference, orsi_visualizer, {("transmitter", "receivers")})


def main():
    set_log_level(LogLevel.WARN)

    app = OrsiInOutBodyApp()
    config_file = os.path.join(os.path.dirname(__file__), "orsi_in_out_body.yaml")
    app.config(config_file)
    app.run()


if __name__ == "__main__":
    main()

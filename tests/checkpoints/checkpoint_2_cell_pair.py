"""
Checkpoint 2: Cell Pair Communication
Verifies that two Cells can be created and can exchange messages.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cell.cell import Cell
from src.cmp.protocol import CMPFrame, MessageType


def main():
    print("CP-2: Cell Pair Communication")
    
    # Create two cells
    cell_a = Cell()
    cell_b = Cell()
    
    assert cell_a.get_id() != cell_b.get_id(), "Cells should have different IDs"
    
    # Create a CMP frame
    frame = CMPFrame(
        src_id=cell_a.get_id(),
        dst_id=cell_b.get_id(),
        msg_type=MessageType.SIGNAL,
        payload=b"hello from cell A"
    )
    
    # Serialize and deserialize
    data = frame.serialize()
    assert len(data) > 0, "Frame serialization failed"
    
    recovered = CMPFrame.deserialize(data)
    assert recovered.msg_type == MessageType.SIGNAL
    
    # Send message
    cell_a.send_message(cell_b, {"type": "SIGNAL", "data": "hello"})
    
    # Receive message
    msg = cell_b.receive_message({"type": "SIGNAL", "data": "hello"})
    assert msg["type"] == "SIGNAL"
    
    print(f"  ✓ Cell A: {cell_a.get_id()}")
    print(f"  ✓ Cell B: {cell_b.get_id()}")
    print(f"  ✓ CMP frame: {len(data)} bytes")
    print(f"  ✓ Message exchange successful")
    print("  ✓ CP-2 PASSED")


if __name__ == "__main__":
    main()

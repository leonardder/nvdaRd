from hwIo.base import IoBase
from typing import Callable, Optional
from ctypes import byref, windll, WinError, c_ulong
from ctypes.wintypes import HANDLE, DWORD
from serial.win32 import FILE_FLAG_OVERLAPPED, INVALID_HANDLE_VALUE, ERROR_IO_PENDING
import winKernel


PIPE_READMODE_BYTE = 0x00000000
PIPE_READMODE_MESSAGE = 0x00000002
PIPE_WAIT = 0x00000000
MAX_PIPE_MESSAGE_SIZE = 1024 * 64


class NamedPipe(IoBase):
	serverProcessId: int

	def __init__(
		self,
		pipeName: str,
		onReceive: Callable[[bytes], None],
		onReadError: Optional[Callable[[int], bool]] = None,
		pipeMode: int = PIPE_READMODE_BYTE
	):
		fileHandle = winKernel.CreateFile(
			pipeName,
			winKernel.GENERIC_READ | winKernel.GENERIC_WRITE,
			0,
			None,
			winKernel.OPEN_EXISTING,
			FILE_FLAG_OVERLAPPED,
			None
		)
		super().__init__(
			fileHandle,
			onReceive,
			onReceiveSize=MAX_PIPE_MESSAGE_SIZE,
			onReadError=onReadError
		)
		if pipeMode:
			dwPipeMode = DWORD(pipeMode)
			if not windll.kernel32.SetNamedPipeHandleState(fileHandle, byref(dwPipeMode), 0, 0):
				raise WinError()
		serverProcessId = c_ulong()
		if not windll.kernel32.GetNamedPipeServerProcessId(HANDLE(fileHandle), byref(serverProcessId)):
			raise WinError()
		self.serverProcessId = serverProcessId.value

	def close(self):
		super().close()
		if hasattr(self, "_file") and self._file is not INVALID_HANDLE_VALUE:
			winKernel.closeHandle(self._file)

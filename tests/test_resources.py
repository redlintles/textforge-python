"""Ownership, binary I/O, callbacks and concurrency at the Python boundary."""

from __future__ import annotations

import errno
import gc
import io
import json
import os
import weakref
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NoReturn

import pytest
from textforge import (
    BatchPool,
    BufferOptions,
    BufferTask,
    FilePath,
    FileTask,
    Observation,
    Observers,
    Pipeline,
    PortableBuffer,
    Processor,
    TextForgeError,
    features,
)


def test_builder_registration_and_snapshot_api(capfd: pytest.CaptureFixture[str]) -> None:
    processor = Processor()
    plan = processor.create_pipeline().add_to_end("!")
    first, second = plan.build(), plan.build()
    assert first != second
    assert processor.process_all(first, "é") == "é!"
    clone = processor.add_transform(processor.get_transform_vec(first))
    assert processor.run_transform(clone, "é") == "é!"
    processor.show_transforms()
    assert first in capfd.readouterr().out
    standalone = Pipeline().push_token(processor.get_transform_vec(first)[0])
    assert standalone.build(processor) in processor.list_transforms()
    with pytest.raises(ValueError, match="requires a processor"):
        standalone.build()
    del processor
    gc.collect()
    assert plan.compile()("x") == "x!"


def test_capabilities_and_pool_lifecycle(tmp_path: Path) -> None:
    assert features().bytecode and features().watchers and features().buffered
    processor = Processor()
    id = processor.create_pipeline().add_to_end("!").build()
    input = tmp_path / "é.txt"
    input.write_text("🍌", encoding="utf-8")
    tasks = [
        FileTask(input, id, tmp_path / "out.txt"),
        FileTask(input, "missing", tmp_path / "bad"),
    ]
    with BatchPool(2) as pool:
        for _ in range(2):
            results = processor.process_batch_in_pool(pool, tasks)
            assert results[0] is None
            assert isinstance(results[1], TextForgeError)
            assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "🍌!"
    assert pool.closed
    pool.close()
    with pytest.raises(ValueError, match="closed"):
        processor.process_batch_in_pool(pool, [])
    for invalid in (-1, 2**64):
        with pytest.raises(OverflowError):
            BatchPool(invalid)
    with pytest.raises(TypeError):
        BatchPool(True)


@pytest.mark.parametrize("text", ["", "é", "🍌", "e\u0301", "a\0b"])
def test_buffer_consumption_and_context_cleanup(tmp_path: Path, text: str) -> None:
    options = BufferOptions(1, tmp_path)
    with PortableBuffer.from_text(text, options) as buffer:
        assert buffer.len_bytes() == len(text.encode())
        assert buffer.is_empty() == (text == "")
        buffer.spill()
        assert buffer.is_spilled()
        assert buffer.read_at(0, 2**64 - 1) == text.encode()
        assert buffer.read_at(2**64 - 1, 1) == b""
        sink = io.BytesIO()
        assert buffer.copy_to(sink) == len(text.encode())
        assert sink.getvalue() == text.encode()
        assert buffer.write_to_file(tmp_path / "saved") == len(text.encode())
        assert buffer.into_string() == text
        assert buffer.closed
        with pytest.raises(ValueError, match="consumed"):
            buffer.len_bytes()
    buffer.close()


def test_buffered_processor_methods_and_failure_consumption(tmp_path: Path) -> None:
    options = BufferOptions(1, tmp_path)
    processor = Processor()
    id = processor.create_pipeline().add_to_end("!").build()
    source = PortableBuffer.from_text("é", options)
    alias = source
    with pytest.raises(TypeError):
        processor.process_all_buffered(1, source)  # type: ignore[arg-type]
    assert not source.closed  # Signature checks happen before ownership transfer.
    result = processor.process_all_buffered(id, source)
    assert alias.closed
    assert result.into_string() == "é!"
    source = PortableBuffer.from_text("é", options)
    assert processor.process_single_buffered('ate "🍌";', source).into_string() == "é🍌"
    input = tmp_path / "input.txt"
    input.write_text("é", encoding="utf-8")
    assert processor.process_file_buffered(id, input, options).into_string() == "é!"
    results = processor.process_batch_buffered(
        [BufferTask(id, input), BufferTask("missing", input)], options
    )
    assert isinstance(results[0], PortableBuffer) and results[0].is_spilled()
    assert results[0].into_string() == "é!"
    assert isinstance(results[1], TextForgeError)
    source = PortableBuffer.from_text("é", options)
    with pytest.raises(TextForgeError):
        processor.process_all_buffered("missing", source)
    assert source.closed
    del processor
    assert PortableBuffer.from_file(input, options).into_string() == "é"


class ChunkReader:
    def __init__(self, data: bytes) -> None:
        self.source = io.BytesIO(data)

    def read(self, maximum: int) -> bytes:
        return self.source.read(min(maximum, 1))


class ShortWriter:
    def __init__(self) -> None:
        self.data = bytearray()

    def write(self, data: bytes) -> int:
        self.data.extend(data[:1])
        return min(1, len(data))


def test_binary_streams_partial_utf8_and_caller_ownership(tmp_path: Path) -> None:
    reader = ChunkReader("é🍌e\u0301".encode())
    ref = weakref.ref(reader)
    buffer = PortableBuffer.from_reader(reader, BufferOptions(1, tmp_path))
    assert not reader.source.closed
    writer = ShortWriter()
    assert buffer.copy_to(writer) == len("é🍌e\u0301".encode())
    assert writer.data.decode() == "é🍌e\u0301"
    del reader
    gc.collect()
    assert ref() is None  # Reading did not retain the Python stream.
    assert buffer.into_string() == "é🍌e\u0301"


@pytest.mark.parametrize("kind", ["raises", "overread", "text", "utf8"])
def test_reader_failure_releases_references(tmp_path: Path, kind: str) -> None:
    class BadReader:
        def read(self, maximum: int) -> bytes:
            if kind == "raises":
                raise ValueError("read failed")
            if kind == "overread":
                return b"x" * (maximum + 1)
            if kind == "text":
                return "wrong"  # type: ignore[return-value]
            return b"\xff"

    reader = BadReader()
    ref = weakref.ref(reader)
    with pytest.raises(TextForgeError) as raised:
        PortableBuffer.from_reader(reader, BufferOptions(1, tmp_path))
    assert raised.value.stage == "execution"
    del raised  # Exception tracebacks legitimately retain Python call arguments.
    del reader
    gc.collect()
    assert ref() is None


@pytest.mark.parametrize("count", [-1, 0, 2**64, True, None])
def test_invalid_writer_count_does_not_consume_buffer(count: object) -> None:
    class BadWriter:
        def write(self, data: bytes) -> int:
            return count  # type: ignore[return-value]

    buffer = PortableBuffer.from_text("é")
    with pytest.raises(TextForgeError):
        buffer.copy_to(BadWriter())
    assert buffer.into_string() == "é"


def test_writer_overcount_and_exception() -> None:
    class BadWriter:
        def write(self, data: bytes) -> int:
            raise LookupError("writer failure")

    class OverWriter:
        def write(self, data: bytes) -> int:
            return len(data) + 1

    buffer = PortableBuffer.from_text("é")
    for writer in (BadWriter(), OverWriter()):
        with pytest.raises(TextForgeError) as raised:
            buffer.copy_to(writer)
        assert raised.value.stage == "execution"
    assert buffer.into_string() == "é"


def test_observation_context_replacement_and_reset(tmp_path: Path) -> None:
    processor = Processor()
    id = processor.create_pipeline().add_to_beginning("🍌").add_to_end("é").build()
    observers = Observers()
    seen: list[Observation] = []

    def capture(observation: Observation) -> str:
        seen.append(observation)
        return observation.current

    observers.set("capture", capture)
    observers.schedule_all("capture")
    observers.set_builtin("size", "current_len_chars")
    observers.schedule_all("size")
    report = tmp_path / "report.json"
    assert processor.process_all_with_watchers(id, "x", observers, report) == "🍌xé"
    assert [(o.before, o.current, o.after) for o in seen] == [
        ("x", "🍌x", "🍌xé"),
        ("🍌x", "🍌xé", None),
    ]
    assert json.loads(report.read_text(encoding="utf-8")) == [
        {"capture": "🍌x", "size": "2"},
        {"capture": "🍌xé", "size": "3"},
    ]
    observers.write_report(tmp_path / "reset.json")
    assert json.loads((tmp_path / "reset.json").read_text(encoding="utf-8")) == []
    observers.set_builtin("capture", "word_count")
    observers.run(Observation("hello world", "", None, "manual"))
    observers.write_report(report)
    assert json.loads(report.read_text(encoding="utf-8")) == [{"capture": "2", "size": "11"}]
    assert "word_count" in observers.builtin_names()
    observers.reset()
    observers.clear()
    with pytest.raises(TextForgeError):
        observers.schedule_all("capture")


def test_callback_exception_preserves_report_and_releases_registration(tmp_path: Path) -> None:
    processor = Processor()
    id = processor.create_pipeline().add_to_end("!").build()
    observers = Observers()

    class Callback:
        def __call__(self, context: Observation) -> str:
            raise ValueError("boom")

    callback = Callback()
    ref = weakref.ref(callback)
    observers.set("bad", callback)
    observers.schedule_all("bad")
    del callback
    gc.collect()
    assert ref() is not None
    report = tmp_path / "report.json"
    report.write_text("unchanged")
    with pytest.raises(TextForgeError) as raised:
        processor.process_all_with_watchers(id, "é", observers, report)
    assert raised.value.stage == "callback" and raised.value.code == 27
    assert "ValueError: boom" in raised.value.message
    assert report.read_text(encoding="utf-8") == "unchanged"
    observers.clear()
    gc.collect()
    assert ref() is None
    assert processor.process_all(id, "x") == "x!"


def test_observer_callback_cycle_is_collectible() -> None:
    class Callback:
        def __init__(self, owner: Observers) -> None:
            self.owner = owner

        def __call__(self, context: Observation) -> str:
            return context.current

    owner = Observers()
    callback = Callback(owner)
    owner.set("cycle", callback)
    ref = weakref.ref(callback)
    del owner, callback
    gc.collect()
    assert ref() is None


def test_processor_reentrancy_and_concurrent_mutation_are_rejected(tmp_path: Path) -> None:
    processor = Processor()
    id = processor.create_pipeline().add_to_end("!").build()
    observers = Observers()

    def callback(context: Observation) -> str:
        with pytest.raises(RuntimeError, match="borrow"):
            processor.process_all(id, "reentrant")
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(processor.remove_transform, id)
            with pytest.raises(RuntimeError, match="borrow"):
                future.result(timeout=5)
        with pytest.raises(RuntimeError, match="borrow"):
            observers.reset()
        return context.current

    observers.set("guard", callback)
    observers.schedule_all("guard")
    assert processor.process_all_with_watchers(id, "x", observers, tmp_path / "report.json") == "x!"
    assert processor.process_all(id, "x") == "x!"


def test_buffer_reentrancy_is_rejected() -> None:
    buffer = PortableBuffer.from_text("é")

    class Writer:
        def write(self, data: bytes) -> int:
            with pytest.raises(RuntimeError, match="borrow"):
                buffer.close()
            return len(data)

    assert buffer.copy_to(Writer()) == 2
    assert buffer.into_string() == "é"


def _create_non_utf8_input(path: bytes) -> None:
    """Probe the filesystem only; EILSEQ means this filename is unsupported."""
    try:
        file = open(path, "wb")
    except OSError as error:
        if error.errno == errno.EILSEQ:
            pytest.skip("filesystem rejects non-UTF-8 filenames (EILSEQ)")
        raise
    with file:
        file.write("é".encode())


def test_non_utf8_probe_skips_only_encoding_rejection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject(path: bytes, mode: str) -> NoReturn:
        raise OSError(errno.EILSEQ, "Illegal byte sequence", path)

    with monkeypatch.context() as patch:
        patch.setattr("builtins.open", reject)
        with pytest.raises(pytest.skip.Exception, match="filesystem rejects non-UTF-8"):
            _create_non_utf8_input(b"nonutf8-\xff.txt")


def test_non_utf8_probe_preserves_other_io_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    failure = PermissionError(errno.EACCES, "Permission denied")

    def reject(path: bytes, mode: str) -> NoReturn:
        raise failure

    with monkeypatch.context() as patch:
        patch.setattr("builtins.open", reject)
        with pytest.raises(PermissionError) as raised:
            _create_non_utf8_input(b"nonutf8-\xff.txt")
    assert raised.value is failure


@pytest.mark.skipif(os.name == "nt", reason="Unix byte path representation")
def test_unix_native_path_representation() -> None:
    # This conversion is valid even when a filesystem cannot create such a name.
    raw = b"nonutf8-\xff.txt"
    native = FilePath.from_native_bytes(raw)
    assert native.to_text() is None
    assert native.to_native_bytes() == raw
    with pytest.raises(TextForgeError) as raised:
        FilePath.from_windows_wide([65])
    assert raised.value.stage == "conversion"


@pytest.mark.skipif(os.name == "nt", reason="Unix byte path representation")
def test_non_utf8_paths_and_surrogateescape(tmp_path: Path) -> None:
    raw = os.fsencode(tmp_path) + b"/nonutf8-\xff.txt"
    _create_non_utf8_input(raw)
    native = FilePath.from_native_bytes(raw)
    assert PortableBuffer.from_file(os.fsdecode(raw)).into_string() == "é"
    processor = Processor()
    id = processor.create_pipeline().add_to_end("!").build()
    output = os.fsencode(tmp_path) + b"/out-\xfe.txt"
    processor.process_file(id, native, output)
    with open(output, "rb") as file:
        assert file.read().decode() == "é!"


@pytest.mark.skipif(os.name != "nt", reason="Windows native wide path representation")
def test_windows_wide_paths() -> None:
    native = FilePath.from_windows_wide([65, 0xD800])
    assert native.to_windows_wide() == [65, 0xD800]
    assert native.to_text() is None
    with pytest.raises(TextForgeError):
        FilePath.from_native_bytes(b"x")


@pytest.mark.skipif(not Path("/proc/self/fd").exists(), reason="Linux descriptor inspection")
def test_spilled_storage_released_after_failure_and_close(tmp_path: Path) -> None:
    def open_spills() -> list[str]:
        paths = []
        for fd in Path("/proc/self/fd").iterdir():
            try:
                target = os.readlink(fd)
            except FileNotFoundError:
                continue
            if str(tmp_path) in target:
                paths.append(target)
        return paths

    assert not open_spills()
    processor = Processor()
    source = PortableBuffer.from_text("é", BufferOptions(1, tmp_path))
    assert open_spills()
    with pytest.raises(TextForgeError):
        processor.process_all_buffered("missing", source)
    assert not open_spills()
    with PortableBuffer.from_text("é", BufferOptions(1, tmp_path)):
        assert open_spills()
    assert not open_spills()


def test_foreign_thread_observers_fail_with_python_error() -> None:
    observers = Observers()
    with ThreadPoolExecutor(max_workers=1) as executor:
        with pytest.raises(RuntimeError, match="creating thread"):
            executor.submit(observers.reset).result(timeout=5)
    observers.clear()


def test_buffer_option_and_read_number_validation(tmp_path: Path) -> None:
    for invalid in (-1, 2**64):
        with pytest.raises(OverflowError):
            BufferOptions(invalid, tmp_path)
    with pytest.raises(TypeError):
        BufferOptions(True, tmp_path)
    with PortableBuffer.from_text("é") as buffer:
        with pytest.raises(TypeError):
            buffer.read_at(True, 1)
        with pytest.raises(OverflowError):
            buffer.read_at(0, -1)

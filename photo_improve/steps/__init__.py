"""Pipeline steps. Each step implements the Step protocol from base.py."""
from photo_improve.steps.base import Step, StepContext, StepResult
from photo_improve.steps.colorize import ColorizeStep
from photo_improve.steps.enhance import EnhanceStep
from photo_improve.steps.face_restore import FaceRestoreStep
from photo_improve.steps.gemini_restore import GeminiRestoreStep
from photo_improve.steps.levels import LevelsStep
from photo_improve.steps.upscale import UpscaleStep

STEP_REGISTRY: dict[str, type[Step]] = {
    "upscale": UpscaleStep,
    "face_restore": FaceRestoreStep,
    "colorize": ColorizeStep,
    "gemini_restore": GeminiRestoreStep,
    "enhance": EnhanceStep,
    "levels": LevelsStep,
}

__all__ = ["Step", "StepContext", "StepResult", "STEP_REGISTRY"]

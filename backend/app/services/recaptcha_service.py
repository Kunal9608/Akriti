import logging
import httpx
from backend.app.config import settings

logger = logging.getLogger(__name__)

def verify_recaptcha_token(token: str) -> bool:
    """
    Verify Google reCAPTCHA v3 token.
    Returns True if verification is disabled or passes successfully.
    """
    if not settings.ENABLE_RECAPTCHA:
        logger.info("reCAPTCHA verification is disabled")
        return True

    if not token:
        logger.warning("reCAPTCHA validation failed: token is missing")
        return False

    # Developer/local test key bypass (Google public test keys)
    if settings.RECAPTCHA_SECRET_KEY in [
        "6LeIxAcTAAAAAGG-vFI1TnFTxWGRtAUMuO_FnD4Q",
        "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
    ]:
        logger.info("reCAPTCHA: Public test key detected. Approving verification automatically.")
        return True

    try:
        url = "https://www.google.com/recaptcha/api/siteverify"
        payload = {
            "secret": settings.RECAPTCHA_SECRET_KEY,
            "response": token
        }

        # Verify with Google API using httpx POST
        response = httpx.post(url, data=payload, timeout=5.0)
        result = response.json()

        success = result.get("success", False)
        score = result.get("score", 0.0)

        logger.info(f"reCAPTCHA validation response: success={success}, score={score}")

        if success:
            # For reCAPTCHA v3, score is 0.0 (bot) to 1.0 (human). Standard threshold is 0.5.
            # Testing keys don't always return the score attribute, so check if it exists.
            if "score" in result and score < 0.5:
                logger.warning(f"reCAPTCHA validation blocked due to low score: {score}")
                return False
            return True

        logger.warning(f"reCAPTCHA validation failed: {result.get('error-codes', 'unknown error')}")
        return False

    except Exception as e:
        logger.error(f"reCAPTCHA verification exception: {e}")
        return False

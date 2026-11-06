"""Worker du workflow conversationnel newsletter-canvas."""

import asyncio

import mistralai.workflows as workflows

from canvas_workflow import NewsletterCanvasWorkflow


async def main() -> None:
    await workflows.run_worker([NewsletterCanvasWorkflow])


if __name__ == "__main__":
    asyncio.run(main())

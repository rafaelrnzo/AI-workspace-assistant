import asyncio

from app.exceptions import GitOperationException


class GitService:

    async def _run_git(self, repo_path: str, *args: str) -> str:
        process = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise GitOperationException(
                f"git {' '.join(args)} failed: {stderr.decode().strip()}"
            )
        return stdout.decode().strip()

    async def clone(self, repo_url: str, target_path: str) -> None:
        process = await asyncio.create_subprocess_exec(
            "git", "clone", repo_url, target_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode != 0:
            raise GitOperationException(
                f"git clone failed: {stderr.decode().strip()}"
            )

    async def checkout(self, repo_path: str, branch: str) -> None:
        await self._run_git(repo_path, "checkout", branch)

    async def create_branch(self, repo_path: str, branch_name: str) -> None:
        await self._run_git(repo_path, "checkout", "-b", branch_name)

    async def get_diff(self, repo_path: str) -> str:
        return await self._run_git(repo_path, "diff")

    async def commit(self, repo_path: str, message: str) -> None:
        await self._run_git(repo_path, "add", ".")
        await self._run_git(repo_path, "commit", "-m", message)

    async def get_current_branch(self, repo_path: str) -> str:
        return await self._run_git(repo_path, "rev-parse", "--abbrev-ref", "HEAD")

import argparse
import pathlib
import subprocess
import json


class Flake:
    def __init__(self, flake_repo: pathlib.Path):
        self.flake_repo = flake_repo

        self.nixpkgs_before: str = self.get_nixpkgs_last_modified()
        self.nixpkgs_after: str

        self.flake_show = {}
        self.get_flake_show()

        self.flake_hosts = []
        self.get_flake_hosts()

        self.build_hosts = []

        self.diff_list = []

    def get_nixpkgs_last_modified(self):
        """
        Get the nixpkgs revision of a flake repository.
        """

        flake_info = subprocess.run(
            cwd=self.flake_repo,
            args=["nix", "flake", "info", "--json"],
            capture_output=True,
            text=True,
        )

        flake_info = json.loads(flake_info.stdout)
        return flake_info["locks"]["nodes"]["nixpkgs"]["locked"]["lastModified"]

    def get_flake_show(self):
        """
        Get the flake info of a flake repository.
        """

        flake_show = subprocess.run(
            cwd=self.flake_repo,
            args=["nix", "flake", "show", "--json"],
            capture_output=True,
            text=True,
        )

        self.flake_show = json.loads(flake_show.stdout)

    def get_flake_hosts(self):
        """
        Get the hosts of a flake repository.
        """

        self.flake_hosts = []

        # print nixosConfigurations from self.flake_show
        for nixos_configuration in self.flake_show["nixosConfigurations"]:
            self.flake_hosts.append(nixos_configuration)

    def add_to_build_hosts(self, host: str):
        """
        Add a host to build hosts if it exists in flake repository.
        """

        if host in self.flake_hosts:
            self.build_hosts.append(host)
        else:
            print(f"Host '{host}' not found in flake repository...")

    def build_host(self, host: str, state: str = ""):
        """
        Build a host in flake repository.
        """

        print(f"Building host '{host}' ({state} update)...")

        subprocess.run(
            cwd=self.flake_repo,
            args=[
                "nix",
                "build",
                "--print-out-paths",
                f'.#nixosConfigurations."{host}".config.system.build.toplevel',
                "--out-link",
                f"result-{host}" if state == "" else f"result-{state}-{host}",
            ],
        )

    def flake_update(self):
        """
        Update a flake repository.
        """

        subprocess.run(
            cwd=self.flake_repo,
            args=["nix", "flake", "update"],
        )

        self.nixpkgs_after = self.get_nixpkgs_last_modified()

    def get_diff_for_host(self, host: str):
        """
        Get the diff for a host in a flake repository.
        """

        print(f"Diffing host '{host}'...")

        result = subprocess.run(
            cwd=self.flake_repo,
            args=[
                "nix",
                "store",
                "diff-closures",
                f"./result-pre-{host}",
                f"./result-post-{host}",
            ],
            capture_output=True,
            text=True,
        )

        # for each line in result.stdout
        for line in result.stdout.split("\n"):
            self.diff_list.append(line)

    def output_diff_list(self):
        """
        Output the diff list.
        """

        # deduplicate diff_list, sort it alphabetically
        self.diff_list = sorted(list(set(self.diff_list)))

        print("\n".join(self.diff_list))

    def save_diff_list(self):
        """
        Save the diff list to a file.
        """

        with open("diff_list.txt", "w") as f:
            f.write("\n".join(self.diff_list))

    def git_revert_update(self):
        """
        Revert the update of a flake repository.
        """

        subprocess.run(
            cwd=self.flake_repo,
            args=["git", "restore", "flake.lock"],
        )


def main():
    """
    Entry point for the CLI.
    """

    parser = argparse.ArgumentParser(description="Build a host in a flake repository.")
    parser.add_argument(
        "--flake_repo", help="Path to flake repository.", required=False
    )
    parser.add_argument("hosts", nargs="+", help="Hosts to build.")

    args = parser.parse_args()

    if args.flake_repo:
        flake = Flake(pathlib.Path(args.flake_repo))
    else:
        flake = Flake(pathlib.Path.cwd())

    for host in args.hosts:
        flake.add_to_build_hosts(host)

    if len(flake.build_hosts) < len(args.hosts):
        print(
            "Some hosts were not found in flake repository!\n"
            + "Those hosts will be ignored!\n"
            + f"The following hosts are available within the flake: {flake.flake_hosts}\n"
            + "----------------------------------------------------------------------------"
        )

    print(f"The following hosts are valid: {flake.build_hosts}")

    # build hosts before update
    for host in flake.build_hosts:
        flake.build_host(host, "pre")

    # update flake repository
    flake.flake_update()

    # build hosts after update
    for host in flake.build_hosts:
        flake.build_host(host, "post")

    # diffing hosts
    for host in flake.build_hosts:
        flake.get_diff_for_host(host)

    print("Went from nixpkgs revision", flake.nixpkgs_before, "to", flake.nixpkgs_after)
    flake.output_diff_list()
    flake.save_diff_list()

    flake.git_revert_update()


if __name__ == "__main__":
    main()

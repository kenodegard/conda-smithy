# This model is also used for generating and automatic documentation for the conda-forge.yml file. The documentation is generated using sphinx and "pydantic-autodoc" extension. For an upstream preview of the documentation, see https://conda-forge.org/docs/maintainer/conda_forge_yml.html.

import warnings
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import (
    AliasChoices,
    BaseModel,
    Field,
    FieldValidationInfo,
    field_validator,
)

from conda_smithy.schema.choices import (
    DefaultTestPlatforms,
    Platforms,
    BotConfigAutoMergeChoice,
    BotConfigInspectionChoice,
    BotConfigSkipRenderChoices,
    ChannelPriorityConfig,
)
from conda_smithy.schema.providers import (
    AzureConfig,
    CIservices,
    CondaBuildTools,
    GithubConfig,
)


def sanitize_remote_ci_setup(package: str) -> str:
    if package.startswith(("'", '"')):
        return package
    elif ("<" in package) or (">" in package) or ("|" in package):
        return '"' + package + '"'
    return package


class PlatformUniqueConfig(BaseModel):
    enabled: bool = Field(
        description="Whether to use extra platform-specific configuration options",
        default=False,
    )


class BotConfig(BaseModel):
    """This dictates the behavior of the conda-forge auto-tick bot which issues automatic version updates/migrations for feedstocks."""

    automerge: Optional[Union[bool, BotConfigAutoMergeChoice]] = Field(
        False,
        description="Automatically merge PRs if possible",
    )

    check_solvable: Optional[bool] = Field(
        False,
        description="Open PRs only if resulting environment is solvable.",
    )

    inspection: Optional[BotConfigInspectionChoice] = Field(
        None,
        description="Method for generating hints or updating recipe",
    )

    abi_migration_branches: Optional[List[str]] = Field(
        None,
        description="List of branches for additional bot migration PRs",
    )

    version_updates_random_fraction_to_keep: Optional[float] = Field(
        None,
        description="Fraction of versions to keep for frequently updated packages",
    )


class CondaForgeChannels(BaseModel):
    """This represents the channels to grab packages from during builds and which channels/labels to push to on anaconda.org after a package has been built. The channels variable is a mapping with sources and targets."""

    sources: Optional[List[str]] = Field(
        default=["conda-forge"],
        description="sources selects the channels to pull packages from, in order",
    )

    targets: Optional[List[List[str]]] = Field(
        default=[["conda-forge", "main"]],
        description="targets is a list of 2-lists, where the first element is the channel to push to and the second element is the label on that channel",
    )


class CondaBuildConfig(BaseModel):
    pkg_format: Optional[Literal["1", "2", "tar"]] = Field(
        description="The package version format for conda build. This can be either '1', '2', or 'tar'. The default is '2'.",
        default="2",
    )

    zstd_compression_level: Optional[int] = Field(
        default=16,
        description="The compression level for the zstd compression algorithm for .conda artifacts. conda-forge uses a default value of 16 for a good compromise of performance and compression.",
    )

    error_overlinking: Optional[bool] = Field(
        default=False,
        description="Enable error when shared libraries from transitive  dependencies are  directly  linked  to any executables or shared libraries in  built packages. This is disabled by default. For more details, see the [conda build documentation](https://docs.conda.io/projects/conda-build/en/stable/resources/commands/conda-build.html).",
    )


class CondaForgeDocker(BaseModel):
    executable: Optional[str] = Field(
        description="The executable for Docker", default="docker"
    )

    fallback_image: Optional[str] = Field(
        description="The fallback image for Docker",
        default="quay.io/condaforge/linux-anvil-comp7",
    )

    command: Optional[str] = Field(
        description="The command to run in Docker", default="bash"
    )

    interactive: Optional[bool] = Field(
        description="Whether to run Docker in interactive mode",
        default=False,
        exclude=True,
    )

    # Deprecated values, if passed should raise errors
    image: Optional[Union[str, None]] = Field(
        description="Setting the Docker image in conda-forge.yml is no longer supported, use conda_build_config.yaml to specify Docker images.",
        default=None,
        exclude=True,
    )

    @field_validator("image", mode="before")
    def image_deprecated(cls, v):
        if v is not None:
            raise ValueError(
                "Setting the Docker image in conda-forge.yml is no longer supported."
                " Please use conda_build_config.yaml to specify Docker images."
            )
        return v


class ShellCheck(BaseModel):
    enabled: bool = Field(
        description="Whether to use shellcheck to lint shell scripts",
        default=False,
    )


class ConfigModel(BaseModel):
    """

    This model describes in detail the top-level fields in  ``conda-forge.yml``. General configuration options are described below within the ``Fields`` specifications. Additional examples are provided as part of the object description. Values and options are subject to change, and will be flagged as Deprecated as appropriate.

    """

    # Values which are not expected to be present in the model dump, are flagged with exclude=True. This is to avoid confusion when comparing the model dump with the default conda-forge.yml file used for smithy or to avoid deprecated values been rendered.

    conda_build: Optional[CondaBuildConfig] = Field(
        default_factory=lambda: CondaBuildConfig(),
    )
    """
    Settings in this block are used to control how `conda build` runs and produces artifacts. The currently supported options are

    .. code-block:: yaml

        conda_build:
        pkg_format: 2    # makes .conda artifacts
        pkg_format: None # makes .tar.bz2 artifacts
        # controls the compression level for .conda artifacts
        # conda-forge uses a default value of 16 since its artifacts
        # can be large. conda-build has a default of 22.
        zstd_compression_level: 16
        error_overlinking: False # enable error when shared libraries from transitive dependencies are directly linked to any executables or shared libraries in built packages

    """

    conda_build_tool: Optional[CondaBuildTools] = Field(
        default="conda-build",
    )
    """
    Use this option to choose which tool is used to build your recipe. The default is ``conda-build``. Other available options are ``conda-build+classic``,``conda-build+conda-libmamba-solver`` and ``mambabuild``.
    """

    conda_solver: Optional[Literal["libmamba", "classic"]] = Field(
        default="libmamba",
    )
    """
    Choose which ``conda`` solver plugin to use for feedstock builds. The default is ``libmamba``. The other option is ``classic``.
    """

    conda_install_tool: Optional[Literal["conda", "mamba"]] = Field(
        default="mamba",
    )
    """
    Use this option to choose which tool is used to provision the tooling in your feedstock.
    """

    conda_forge_output_validation: Optional[bool] = Field(
        default=True,
    )
    """
    This field must be set to ``True`` for feedstocks in the ``conda-forge`` GitHub
    organization. It enables the required feedstock artifact validation as described in `Output Validation and Feedstock Tokens <https://conda-forge.org/docs/maintainer/infrastructure.html#output-validation>`_.
    """

    github: Optional[GithubConfig] = Field(
        default_factory=lambda: GithubConfig(),
    )
    """
    Mapping for GitHub-specific configuration options. The
    defaults are as follows:

    .. code-block:: yaml

        github:
        # name of the github organization
        user_or_org: conda-forge
        # repository name, usually filled in automatically
        repo_name: ""
        # branch name to execute on
        branch_name: main
        # branch name to use for rerender+webservices github actions and
        # conda-forge-ci-setup-feedstock references
        tooling_branch_name: main
    """

    bot: Optional[BotConfig] = Field(
        default_factory=lambda: BotConfig(),
    )
    """
    This dictates the behavior of the conda-forge auto-tick bot which issues automatic version updates/migrations for feedstocks. The current options are

    .. code-block:: yaml

        bot:
        # can the bot automerge PRs it makes on this feedstock
        automerge: true
        # only automerge on successful version PRs, migrations are not automerged
        automerge: 'version'
        # only automerge on successful migration PRs, versions are not automerged
        automerge: 'migration'

        # only open PRs if resulting environment is solvable, useful for tightly coupled packages
        check_solvable: true

        # The bot.inspection key in the conda-forge.yml can have one of six possible values:
        inspection: hint  # generate hints using source code (backwards compatible)
        inspection: hint-all  # generate hints using all methods
        inspection: hint-source  # generate hints using only source code
        inspection: hint-grayskull  # generate hints using only grayskull
        inspection: update-all  # update recipe using all methods
        inspection: update-source  # update recipe using only source code
        inspection: update-grayskull  # update recipe using only grayskull

        # any branches listed in this section will get bot migration PRs in addition
        # to the default branch
        abi_migration_branches:
            - v1.10.x

        version_updates:
            # use this for packages that are updated too frequently
            random_fraction_to_keep: 0.1  # keeps 10% of versions at random

    The ``abi_migration_branches`` feature is useful to, for example, add a
    long-term support (LTS) branch for a package.
    """

    build_platform: Optional[Dict[Platforms, Platforms]] = Field(
        default_factory=dict,
    )
    """
    This is a mapping from the target platform to the build platform for the package to be built.
    For example, the following builds a ``osx-64`` package on the ``linux-64``
    build platform using cross-compiling.

    .. code-block:: yaml

        build_platform:
        osx_64: linux_64

    Leaving this field empty implicitly requests to build a package natively. i.e.

    .. code-block:: yaml

        build_platform:
        linux_64: linux_64
        linux_ppc64le: linux_ppc64le
        linux_aarch64: linux_aarch64
        osx_64: osx_64
        osx_arm64: osx_arm64
        win_64: win_64
    """

    build_with_mambabuild: Optional[bool] = Field(
        default=True,
    )
    """
    Configures the conda-forge CI to run a debug build using the ``mamba`` solver. More information can be found in the `mamba docs <https://conda-forge.org/docs/maintainer/maintainer_faq.html#mfaq-mamba-local>`_.

    .. code-block:: yaml

        build_with_mambabuild:
        True
    """

    channel_priority: Optional[ChannelPriorityConfig] = Field(
        default="strict",
    )
    """
    The channel priority level for the conda solver during feedstock builds. This can be one of `strict`, `flexible`, or `disabled`. For more information, see the `Strict channel priority <https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-channels.html#strict-channel-priority>`_ section on conda documentation.
    """

    channels: Optional[CondaForgeChannels] = Field(
        default_factory=lambda: CondaForgeChannels(),
    )
    """
    This represents the channels to grab packages from during builds and which channels/labels to push to on anaconda.org after a package has been built. The ``channels`` variable is a mapping with ``sources`` and ``targets``, as follows:

    .. code-block:: yaml

        channels:
        # sources selects the channels to pull packages from, in order.
        sources:
            - conda-forge
            - defaults
        # targets is a list of 2-lists, where the first element is the
        # channel to push to and the second element is the label on that channel
        targets:
            - ["conda-forge", "main"]
    """

    choco: Optional[List[str]] = Field(
        default_factory=list,
    )
    """
    This parameter allows for conda-smithy to run chocoloatey installs on Windows when additional system packages are needed. This is a list of strings that represent package names and any additional parameters. For example,

    .. code-block:: yaml

        choco:
        # install a package
        - nvidia-display-driver

        # install a package with a specific version
        - cuda --version=11.0.3

    This is currently only implemented for Azure Pipelines. The command that is run is
    ``choco install {entry} -fdv -y --debug``.  That is, ``choco install`` is executed
    with a standard set of additional flags that are useful on CI.
    """

    docker: Optional[CondaForgeDocker] = Field(
        default_factory=lambda: CondaForgeDocker(),
    )
    """
    This is a mapping for Docker-specific configuration options. The defaults are as follows:

    .. code-block:: yaml

        docker:
        executable: docker
        image: "condaforge/linux-anvil-comp7"
        command: "bash"
        interactive: True
    """

    idle_timeout_minutes: Optional[int] = Field(
        default=None,
    )
    """
    Configurable idle timeout.  Used for packages that don't have chatty enough builds. Applicable only to circleci and travis

    .. code-block:: yaml

        idle_timeout_minutes: 60
    """

    win_64: Optional[PlatformUniqueConfig] = Field(
        default_factory=lambda: PlatformUniqueConfig(),
        validation_alias=AliasChoices("win_64", "win"),
    )
    """
    Windows-specific configuration options. This is largely an internal setting and should not normally be manually modified.

    .. code-block:: yaml

        win:
            enabled: False

    As show above by the example, aliasing is supported for the win platform and will be converted to the appropriate platform name (win_64) during build.
    """

    osx_64: Optional[PlatformUniqueConfig] = Field(
        default_factory=lambda: PlatformUniqueConfig(),
        validation_alias=AliasChoices("osx_64", "osx"),
    )
    """
    OSX-specific configuration options. This is largely an internal setting and should not normally be manually modified.

    .. code-block:: yaml

        osx:
            enabled: False

    As show above by the example, aliasing is supported for the osx platform and will be converted to the appropriate platform name (osx_64) during build.
    """

    osx_arm64: Optional[PlatformUniqueConfig] = Field(
        default_factory=lambda: PlatformUniqueConfig(),
    )
    """
    OSX-specific (ARM) configuration options. This is largely an internal setting and should not normally be manually modified.
    """

    linux_64: Optional[PlatformUniqueConfig] = Field(
        default_factory=lambda: PlatformUniqueConfig(),
        validation_alias=AliasChoices("linux_64", "linux"),
    )
    """
    Linux-specific configuration options. This is largely an internal setting and should not normally be manually modified.

    .. code-block:: yaml

        linux:
            enabled: False

    As show above by the example, aliasing is supported for the linux platform and will be converted to the appropriate platform name (linux_64) during build.
    """

    linux_aarch64: Optional[PlatformUniqueConfig] = Field(
        default_factory=lambda: PlatformUniqueConfig(),
    )
    """
    ARM-specific configuration options. This is largely an internal setting and should not normally be manually modified.

    .. code-block:: yaml

        linux_aarch64:
            enabled: False
    """

    linux_ppc64le: Optional[PlatformUniqueConfig] = Field(
        default_factory=lambda: PlatformUniqueConfig(),
    )
    """
    PPC-specific configuration options. This is largely an internal setting and should not normally be manually modified.

    .. code-block:: yaml

        linux_ppc64le:
            enabled: False
    """

    linux_s390x: Optional[PlatformUniqueConfig] = Field(
        default_factory=lambda: PlatformUniqueConfig(),
    )
    """
    s390x-specific configuration options. This is largely an internal setting and should not normally be manually modified.

    .. code-block:: yaml

        linux_s390x:
            enabled: False
    """

    linux_armv7l: Optional[PlatformUniqueConfig] = Field(
        default_factory=lambda: PlatformUniqueConfig(),
    )
    """
    ARM-specific configuration options. This is largely an internal setting and should not normally be manually modified.

    .. code-block:: yaml

        linux_armv7l:
            enabled: False
    """

    @field_validator(
        "win_64",
        "osx_64",
        "linux_64",
        "linux_aarch64",
        "linux_ppc64le",
        "linux_s390x",
        "linux_armv7l",
        mode="before",
    )
    @classmethod
    def validate_platform(
        cls,
        field_value,
        _info: FieldValidationInfo,
    ):
        """
        Validator function for platform settings.

        This function checks if the platform is disabled but also in the build_platform list,
        and raises a ValueError with an appropriate error message if that's the case.

        :param cls: The class where the validator is defined.
        :param field_value: The value of the platform field.
        :param _info: Information about the field being validated.
        :return: The original field_value.
        """
        print(f"{cls}: Field value {field_value}")
        # Check if field_value is a dictionary and extract the 'enabled' key if present
        if isinstance(field_value, dict):
            _field_value = field_value.get("enabled", None)
        else:
            _field_value = getattr(field_value, "enabled", None)

        # Check if the platform is disabled but also in the build_platform list
        if _field_value is False and _info.field_name in _info.data.get(
            "build_platform", []
        ):
            error_message = (
                f"Platform {field_value} is disabled but is also a build platform."
                " Please enable the platform or remove it from build_platform."
            )
            raise ValueError(error_message)

        return field_value

    noarch_platforms: Optional[List[Platforms]] = Field(
        default_factory=lambda: ["linux_64"],
    )
    """
    Platforms on which to build noarch packages. The preferred default is a
    single build on ``linux_64``.

    .. code-block:: yaml

        noarch_platforms: linux_64

    To build on multiple platforms, e.g. for simple packages with platform-specific
    dependencies, provide a list.

    .. code-block:: yaml

        noarch_platforms:
        - linux_64
        - win_64
    """

    os_version: Optional[Dict[Platforms, Union[str, None]]] = Field(
        default_factory=dict,
    )
    """
    This key is used to set the OS versions for `linux_*` platforms. Valid entries map a linux platform and arch to either `cos6` or `cos7`. Currently `cos6` is the default for `linux-64`. All other linux architectures use CentOS 7. Here is an example that enables CentOS 7 on ``linux-64`` builds

    .. code-block:: yaml

        os_version:
            linux_64: cos7
    """

    provider: Optional[
        Dict[Platforms, Union[List[CIservices], CIservices, bool, None]]
    ] = Field(
        default_factory=dict,
    )
    """
    The ``provider`` field is a mapping from build platform (not target platform) to CI service. It determines which service handles each build platform. If a desired build platform is not available with a selected provider (either natively or with emulation), the build will be disabled. Use the ``build_platform`` field to manually specify cross-compilation when no providers offer a desired build platform.

    The following are available as supoprted build platforms:

    * ``linux_64``
    * ``osx_64``
    * ``win_64``
    * ``linux_aarch64``
    * ``linux_ppc64le``

    The following CI services are available:

    * ``azure``
    * ``circle``
    * ``travis``
    * ``appveyor``
    * ``None`` or ``False`` to disable a build platform.
    * ``default`` to choose an appropriate CI (only if available)

    For example, switching linux_64 & osx_64 to build on Travis CI, with win_64 on Appveyor:

    .. code-block:: yaml

        provider:
        linux_64: travis
        osx_64: travis
        win_64: appveyor

    Currently, x86_64 platforms are enabled, but other build platforms are disabled by default. i.e. an empty
    provider entry is equivalent to the following:

    .. code-block:: yaml

        provider:
        linux_64: azure
        osx_64: azure
        win_64: azure
        linux_ppc64le: None
        linux_aarch64: None

    To enable ``linux_ppc64le`` and ``linux_aarch64`` add the following:

    .. code-block:: yaml

        provider:
        linux_ppc64le: default
        linux_aarch64: default
    """

    package: Optional[str] = Field(
        default=None,
        description="Default location for a package feedstock directory basename.",
    )

    recipe_dir: Optional[str] = Field(
        default="recipe",
    )
    """
    The relative path to the recipe directory. The default is:

    .. code-block:: yaml

        recipe_dir: recipe
    """

    remote_ci_setup: Optional[List[str]] = Field(
        default_factory=lambda: ["conda-forge-ci-setup=3"],
    )
    """
    This option can be used to override the default `conda-forge-ci-setup` package. Can be given with ``${url or channel_alias}::package_name``, defaults to conda-forge channel_alias if no prefix is given. defaults to conda-forge
    channel_alias if no prefix is given.

    .. code-block:: yaml

        remote_ci_setup: "conda-forge-ci-setup=3"
    """

    @field_validator("remote_ci_setup", mode="before")
    def validate_remote_ci_setup(cls, remote_ci_setup):
        """
        Validator function for remote_ci_setup field.

        This function sanitizes the remote_ci_setup packages and returns the sanitized list.

        :param cls: The class where the validator is defined.
        :param remote_ci_setup: The list of remote_ci_setup packages.
        :return: The sanitized list of remote_ci_setup packages.
        """
        _sanitized_remote_ci_setup = []
        for package in remote_ci_setup:
            _sanitized_remote_ci_setup.append(
                sanitize_remote_ci_setup(package)
            )
        return _sanitized_remote_ci_setup

    shellcheck: Optional[ShellCheck] = Field(
        default=None,
    )
    """
    Shell scripts used for builds or activation scripts can be linted with shellcheck. This option can be used to enable shellcheck and configure its behavior. This is not enabled by default, but can be enabled like so:

    .. code-block:: yaml

        shellcheck:
        enabled: True

    """

    skip_render: Optional[List[BotConfigSkipRenderChoices]] = Field(
        default_factory=list,
        description="This option specifies a list of files which `conda smithy` will skip rendering.",
    )
    """
    This option specifies a list of files which `conda smithy` will skip rendering. This is useful for files that are not templates, but are still in the recipe directory. The default value is an empty list [ ], i.e. all these four files will be generated by conda smithy.
    For example, if you want to skip rendering the .gitignore and LICENSE.txt files, you can add the following:

    .. code-block:: yaml

        skip_render:
        - .gitignore
        - LICENSE.txt
    """

    templates: Optional[Dict[str, str]] = Field(
        default_factory=dict,
    )
    """
    This is mostly an internal field for specifying where template files reside. You shouldn't need to modify it.
    """

    test_on_native_only: Optional[bool] = Field(
        default=False,
    )
    """
    This was used for disabling testing for cross-compiling.

    .. note::
        This has been deprecated in favor of the top-level `test` field. It is now mapped to `test: native_and_emulated`.
    """

    test: Optional[DefaultTestPlatforms] = Field(
        default=None,
    )
    """
    This is used to configure on which platforms a recipe is tested. The default is ``all``.

    .. code-block:: yaml

        test: native_and_emulated

    Will do testing only if the platform is native or if there is an emulator.

    .. code-block:: yaml

        test: native

    Will do testing only if the platform is native.
    """

    upload_on_branch: Optional[str] = Field(
        default=None,
    )
    """
    This parameter restricts uploading access on work from certain branches of the
    same repo. Only the branch listed in ``upload_on_branch`` will trigger uploading
    of packages to the target channel. The default is to skip this check if the key
    ``upload_on_branch`` is not in ``conda-forge.yml``. To restrict uploads to the
    main branch:

    .. code-block:: yaml

        upload_on_branch: main
    """

    config_version: Optional[str] = Field(
        default="2",
    )
    """
    The version of the `conda-forge.yml` specification. This should not be manually modified.
    """

    exclusive_config_file: Optional[str] = Field(
        default=None,
    )
    """
    Exclusive conda-build config file to replace `conda-forge-pinning`. For advanced usage only.
    """

    compiler_stack: Optional[str] = Field(
        default="comp7",
    )
    """
    Compiler stack environment variable. This is used to specify the compiler stack to use for builds. The default is ``comp7``.

    .. code-block:: yaml

        compiler_stack: comp7
    """

    min_py_ver: Optional[str] = Field(
        default="27",
    )
    """
    Minimum Python version. This is used to specify the minimum Python version to use for builds. The default is ``27``.

    .. code-block:: yaml

        min_py_ver: 27
    """

    max_py_ver: Optional[str] = Field(
        default="37",
    )
    """
    Maximum Python version. This is used to specify the maximum Python version to use for builds. The default is ``37``.

    .. code-block:: yaml

        max_py_ver: 37
    """

    min_r_ver: Optional[str] = Field(
        default="34",
    )
    """
    Minimum R version. This is used to specify the minimum R version to use for builds. The default is ``34``.

    .. code-block:: yaml

        min_r_ver: 34
    """

    max_r_ver: Optional[str] = Field(
        default="34",
        description="Maximum R version.",
    )
    """
    Maximum R version. This is used to specify the maximum R version to use for builds. The default is ``34``.

    .. code-block:: yaml

        max_r_ver: 34
    """

    private_upload: Optional[bool] = Field(
        default=False,
        description="Whether to upload to a private channel.",
    )
    """
    Whether to upload to a private channel. The default is ``False``.

    .. code-block:: yaml

        private_upload: False
    """

    secrets: Optional[List[str]] = Field(
        default_factory=list,
    )
    """
    List of secrets to be used in GitHub Actions. The default is an empty list and will not be used.
    """

    clone_depth: Optional[int] = Field(
        default=None,
    )
    """
    The depth of the git clone. The default is ``None``.
    """

    timeout_minutes: Optional[int] = Field(
        default=None,
    )
    """
    The timeout in minutes for all platforms CI jobs. The default is ``None``. If passed alongside with Azure, it will be used as the default timeout for Azure Pipelines jobs.
    """

    ###################################
    ####       CI Providers        ####
    ###################################
    travis: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
    )
    """
    Travis CI settings. This is usually read-only and should not normally be manually modified. Tools like conda-smithy may modify this, as needed.
    """

    circle: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
    )
    """
    Circle CI settings. This is usually read-only and should not normally be manually modified. Tools like conda-smithy may modify this, as needed.
    """

    appveyor: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
    )
    """
    AppVeyor CI settings. This is usually read-only and should not normally be manually modified. Tools like conda-smithy may modify this, as needed.
    """

    azure: Optional[AzureConfig] = Field(
        default_factory=lambda: AzureConfig(),
    )
    """
    Azure Pipelines CI settings. This is usually read-only and should not normally be manually modified. Tools like conda-smithy may modify this, as needed. For example:

    .. code-block:: yaml

        azure:
        # flag for forcing the building all supported providers
        force: False
        # toggle for storing the conda build_artifacts directory (including the
        # built packages) as an Azure pipeline artifact that can be downloaded
        store_build_artifacts: False
        # toggle for freeing up some extra space on the default Azure Pipelines
        # linux image before running the Docker container for building
        free_disk_space: False
        # limit the amount of CI jobs running concurrently at a given time
        # each OS will get its proportional share of the configured value
        max_parallel: 25


    .. _self-hosted_azure-config:

    Below is an example configuration for setting up a self-hosted Azure agent for Linux:

    .. code-block:: yaml

        azure:
            settings_linux:
            pool:
                name: your_local_pool_name
                demands:
                - some_key -equals some_value
            workspace:
                clean: all
            strategy:
                maxParallel: 1

    Below is an example configuration for adding a swapfile on an Azure agent for Linux:

    .. code-block:: yaml

        azure:
            settings_linux:
                swapfile_size: 10GiB
    """

    drone: Optional[Dict[str, str]] = Field(
        default_factory=dict,
    )
    """
    Drone CI settings. This is usually read-only and should not normally be manually modified. Tools like conda-smithy may modify this, as needed.
    """

    github_actions: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
    )
    """
    GitHub Actions CI settings. This is usually read-only and should not normally be manually modified. Tools like conda-smithy may modify this, as needed.
    """

    woodpecker: Optional[Dict[str, str]] = Field(
        default_factory=dict,
    )
    """
    Woodpecker CI settings. This is usually read-only and should not normally be manually modified. Tools like conda-smithy may modify this, as needed.
    """

    @field_validator(
        "travis",
        "circle",
        "appveyor",
        "drone",
        "azure",
        "github_actions",
        "woodpecker",
        mode="before",
    )
    def validate_providers(
        cls,
        providers,
        _info: FieldValidationInfo,
    ):
        """
        Validator function for CI provider settings.

        This function checks if the 'enabled' parameter is set for CI providers and raises a warning if it is set.

        :param cls: The class where the validator is defined.
        :param providers: The CI provider settings.
        :param _info: Information about the field being validated.
        :return: The original providers dictionary.
        """
        if providers.get("enabled", None):
            warnings.warn(
                f"It is not allowed to set the `enabled` parameter for {_info.field_name}."
                " All CIs are enabled by default. To disable a CI, please"
                " add `skip: true` to the `build` section of `meta.yaml`"
                " and an appropriate selector so as to disable the build."
            )
        return providers

    ###################################
    ####       Deprecated          ####
    ###################################

    # Deprecated values, if passed should raise errors, only present for validation
    # Will not show up in the model dump, due to exclude=True

    matrix: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        exclude=True,
    )
    """
    Build matrices were used to specify a set of build configurations to run for each package pinned dependency. This has been deprecated in favor of the provider field. More information can be found in the `conda-forge docs <https://conda-forge.org/docs/maintainer/knowledge_base.html#build-matrices>`_.
    """

    @field_validator("matrix", mode="before")
    def matrix_deprecated(cls, v):
        """
        Validator function for 'matrix' field.

        This function checks if the 'matrix' field is not None, and if it's not None,
        it raises a ValueError with migration instructions.

        :param cls: The class where the validator is defined.
        :param v: The value of the 'matrix' field.
        :return: The original value 'v' if it's None.
        """
        if v is not None:
            raise ValueError(
                "Cannot rerender with matrix in conda-forge.yml."
                " Please migrate matrix to conda_build_config.yaml and try again."
                " See `here <https://github.com/conda-forge/conda-smithy/wiki/Release-Notes-3.0.0.rc1>`_ for more info."
            )
        return v

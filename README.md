# Tool for picking commits from the AOSP

A CLI tool for picking bazel plugin commits from the [AOSP](https://cs.android.com/android-studio/platform/tools/adt/idea/+/mirror-goog-studio-main:aswb/) to the git [repository](https://github.com/bazelbuild/intellij). 

### Setup

The tool can be installed into a local virtual environment using the Makefile:

```bash
make install
```

After the tool is installed, it can be executed from inside the virtual environment. To activate the virtual environment, run the following command:

```bash
source .venv/bin/activate
```

The tool needs access to the git repository. The path to repository can be specified for every command using the `--repo` option or by exporting the `REPO` environment variable.

### Commit Pick

To pick a commit from the AOSP by its hash run the following command:

```bash
aosp pick <hash>
```

Make sure to check out the right branch in the git repository where the commit should be applied. 

### Commit Review

To review a commit, run the following command and specify the hash of the already applied commit:

```bash
aosp review <hash> # where <hash> is hash in bazelbuild/intellij

# effectively you might need to do 
# git fetch origin pull/<id>/head && aosp review FETCH_HEAD
```

The tool generates a diff between the patch applied to the git repository and the patch applied to the AOSP.

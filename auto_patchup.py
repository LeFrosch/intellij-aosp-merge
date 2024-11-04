import subprocess
import sys

from patchup import (
    aosp_remote,
    aosp_fetch,
    patch_generate,
    patch_apply,
    generate_log,
    abort_am,
)

repo = '/Volumes/Projects/bazel/intellij'

commits = [
    "8cca96f3feeccb769ff46c7020059ed98c3c7aa6",
    "2af5de0bb113332b2efb6311a98bc4cd8079f642",
    "8f09f18928e306264aff10dc1859f5fc9bdd9a6a",
    "e460f4d2ed682ce0d70a6c5442e53ef2cea1f924",
    "02167ba65d2a02a2b65dcae3fdababbacb91dcab",
    "14c48e5ce89f1d6314ff9829b605d591b63dbd29",
    "19d29071db190bcb66427a334f3447e163fb0d56",
    "1601e6813a829e3f628c2ddffb3a5d3d99e44ad0",
    "b108f0fb446f246b75bf9555c4f4825ecc2c32c9",
    "1dfe1bfbe47e788dbfe0b1b5318eba3d10db482d",
    "6ee8fec3e47ad9e1dd318f4f9f858bdb8e81f2ca",
    "2bb109047e7514ca8b28b97d57cb3484583b438e",
    "15925d95666ea634256f69b7fc1935a8a7b16096",
    "55cfa655be0b6f57d8fe4c69e52369a7f0cff328",
    "a58f1f7418437dd3729f36966951661f203053d6",
    "87661c3a686a79d3be5479d58fd09b35ada74c71",
    "49f1417f9c11b4579287709dc5eddf8d468d4271",
    "1f70eda5d83889e02aac5eb64e149ad035312ae8",
    "89f21f6dfc0769419d58bcc6c8ce5a74fa156036",
    "c951c0c4a9eee40265735c676b4a3503ba1fb754",
    "173997ad2019d1f7fc08c12d54fc49e5d2bddead",
    "1750b5a8694b32f024b64446b2a4cc9f527124e0",
    "e044b691c0c7f86104f131013aa5cb78f9c77d63",
    "e76ca43d11e2404a95289454996d130cc004a965",
    "dfd23fdab79918058440e59c825071aaaecc68e0",
    "d8b9b2f9375da0bda45383acb91555c8a84edbf6",
    "1e72e4a9932d5ec0ecb103dc07ee75e3eda6ce80",
    "1958c390fe994e3c0cda93c20a5dd7e92940dba9",
    "51986036389adb93adc61deb56b1c7f7405dd366",
    "c0ee4c754d28cd246d4c40c498176266c6766f81",
    "9f2bdfc2c793f77a8bd313ec3773880379333c04",
    "849587dab42bd823d0d7a6c1bca87e80f1bbd29d",
    "211903992d0bff4d5236a7ad341be3b5fe795b38",
    "bcfadb67403db980511bea766f1c8477c0aa1844",
    "4259fe4964d94a433bd7bda24ee8e8a8c536e69f",
    "b4a02554c39c29c5ca777d46143ee59335b4ad8d",
    "a7c1aa63d214699fcb9061e235060fd672570e43",
    "6fdf79cb922f07ab4d083d5b8c89a798a000b043",
    "f3858b9b99fee7079308a5d82c9cff131aea2e65",
    "4c92354fd597aa7ef4844d3e5e690a1b70539290",
    "5dae7e27ae1ff41501ff7ffe862119bdabaf8ef1",
    "30f521605822a9120678e4316e5978a34c5ae3e1",
    "84e61bb7efe3d82c9920889f03f50015369b1310",
    "7af1ba85bfa2e6821be75cc7e189dfac823d4d23",
    "021fa52b4e3d2b3af17e4fb6e93a506d61ed4385",
    "d7052f0319435df621f31befa958d651834177ba",
    "8f4770951800c30753b6cb8625a1add039a36158",
    "7b4aa0433640e5d39141f86a3121f6abcf467672",
    "f5b35dce9050c31404e211e47c60362c66c4c4c3",
    "5597ed20d302d2af3bdea0fb7acbebd7ba7c0aea",
    "e10a072e8183210fff6f719269a9fbb479ff6108",
    "13119e8b66b15a1342253b7e6bbe5c5acab047e5",
    "16d3115bc777f9ddeb32f7270f643455297683f7",
    "5c518fa1757598525f3421487e46665c9df3bcd4",
    "b1fe2e07d2847b8d5b9b6072828a686763196cf3",
    "48458504e1f3c0bd3d3a10c9f8da3cc5607bcddb",
    "958a6bda20a27abcd7ebd218fd52fce2fc5a6bee",
    "35f46f4bc524961a6f72262c6618c3a072bd492e",
    "36a88eda0bb9d7eef1dc2b672a35a10194e40ca5",
    "94f8bf741014863b4af3247e007185530441f891",
    "4c245e80df91ba178049b1a7751a63955eddbe53",
    "2c373a0631058fb2880362fb260a58b2f52c68aa",
    "c8c49a9a5165c95d90cd09b6783c2cc62738eb9f",
    "46d1745775b1b007472aa3a23e14dddb0a0eafc9",
    "3dcb412e8df1b84179d1058df2f16c39bb6e3538",
    "759ff9a0a665fc36ca21e92d973fe4190b0d9333",
    "c1930315adc4f9059838a7c2d32ec0ac7f48e7c6",
    "a39aed36c5b19258344672918a771f32c74b8e1d",
    "2401655e1e7ea05ab225a886436e4a023e42122e",
    "bb78ce8e198735e8098880ae7a16844f26d26e98",
    "bf72f60ebbb555413db30a7b8ccfb15e2808aef8",
    "7387ba2734e1166ed62c59855b3d61787ef48662",
    "39a81c4a4061ff8c7910b68844eba3aa88fd5a84",
    "eaba2a13faf2d9941009e860bc2687f16a027a3e",
    "0d704b87e5dbbbc34e719aecbdd69d9efcd0db10",
    "93fa3c49f29ab8dc7c97824e87e6a9bdda76ec3a",
    "18e374dc4b328f8e64b1bfba0949e7ec0a00e344",
    "bfedef8169cc5ac0dc1b7a01c6e162b81dac6ccf",
    "103b4900bb821081e276ab0f2ec204a4ed53ce27",
    "fb8ea8ffee880557da947f5d6b989b6dd96de4e0",
    "744df3bcd1491460968efc8d94aa54998eac9600",
    "f001cc8cba854683de6d125416b3481df7af1ec6",
    "62682fcc4673e488bb8f79379449c7543c7ec56c",
    "f0b0cc79040a2b0c969c82bb04aeb8e1906816f1",
    "e25ef9c78b6fe52524b926c810b33beccedd1988",
    "aa982c800af6f69d7f13dc6f578f66c3e300f901",
    "bc8299705b148f2768dd8a39e0b8ee490fee01c8",
    "6d15c5d225836e3228c4e86e3c81b08b0e799fc0",
    "304147a2b7f8e62af3155cd335423d2383073516",
    "b18450c697e56287fb7be165b83f64a8c1b2479b",
    "7629a11cb2cd2c344f465abd1f3fc3cf0049364c",
    "6f384175938a9ab8c85b5ecbe15d97029d5f1a5a",
    "d2d209c72627569603f3834f062af382a36fe1ac",
    "519d8c9ecf5caa7f11de224b6423203fd9ddcc63",
    "a2878fdcc55358acdd14e1074c3030c97a516610",
    "69830fcd16f3d3b1090fef59d3408af7b346ad8c",
    "3184086e930101a1aab3b9c7d2093595093bd9ed",
    "be167de007bc128bdb669bfcc1a0c3735d8c7cbf",
    "cb3f07cd985b75d7c56f8f42796dca709da95e6b",
]


def patch(commit: str) -> bool:
    patch = patch_generate(commit)
    success = patch_apply(patch, reject=False)

    if (success):
        print('-> patch applied')
        return True

    answer = input('-> 3way merge failed, fallback to no-3way? [y/n]')
    if (answer != 'y'):
        print('-> patch failed')
        return

    abort_am()
    success = patch_apply(patch, reject=True)

    if (success):
        print('-> patch applied')
    else:
        print('-> patch applied with rejects')

    return success


def test(target: str):
    print('-> testing %s' % target)

    while True:
        success = subprocess.run(
            [
                'bazel',
                'test',
                target,
                '--define=ij_product=intellij-ue-2024.2',
            ],
            cwd=repo,
            stderr=sys.stdout,
            stdout=sys.stdout,
        ).returncode == 0

        if (success):
            print('-> test passed %s' % target)
            return
        else:
            print('-> test failed %s' % target)
            input('-> press any key to retry test')


def main():
    aosp_remote()
    aosp_fetch()

    for commit in commits:
        message = generate_log(commit, '%s')
        print('-> processing commit: %s - %s' % (commit, message))

        answer = input('-> skip this commit? [y/n]')
        if (answer != 'n'):
            print('-> skipping commit')
            continue

        success = patch(commit)

        if (not success):
            input('-> patch failed, press any key to continue')

        test('//:ijwb_ue_tests')
        test('//querysync/...')


if __name__ == '__main__':
    main()

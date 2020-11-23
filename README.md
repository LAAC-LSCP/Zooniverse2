# Zooniverse2

Split audios in chunks and uploads them to zooniverse

## Installation

```bash
git clone https://github.com/LAAC-LSCP/Zooniverse2.git
cd Zooniverse2
pip install -r requirements.txt
```

## Usage

```bash
zooniverse.py [-h] --destination DESTINATION --project-slug
                     PROJECT_SLUG --subject-set SUBJECT_SET --sample-size
                     SAMPLE_SIZE --zooniverse-login ZOONIVERSE_LOGIN
                     --zooniverse-pwd ZOONIVERSE_PWD [--threads THREADS]
                     [--target-speaker-type {CHI,OCH,FEM,MAL}]
                     path
```

<table>
<tr>
    <th>argument</th>
    <th>description</th>
    <th>default value</th>
</tr>
<tr>
    <td>path</td>
    <td>path to the dataset</td>
    <td></td>
</tr>
<tr>
    <td>destination</td>
    <td>where to write the output metadata and files. metadata will be saved to $destination/chunks.csv and audio chunks to $destination/chunks.</td>
    <td></td>
</tr>
<tr>
    <td>project-slug</td>
    <td>Zooniverse project slug (e.g.: lucasgautheron/my-new-project)</td>
    <td></td>
</tr>
<tr>
    <td>subject-set</td>
    <td>prefix for the subject set</td>
    <td></td>
</tr>
<tr>
    <td>sample-size</td>
    <td>how many vocalization events per recording</td>
    <td></td>
</tr>
<tr>
    <td>target-speaker-type</td>
    <td>speaker type to get chunks from</td>
    <td>CHI</td>
</tr>
<tr>
    <td>zooniverse-login</td>
    <td>zooniverse login</td>
    <td></td>
</tr>
<tr>
    <td>zooniverse-pwd</td>
    <td>zooniverse password</td>
    <td></td>
</tr>
<tr>
    <td>threads</td>
    <td>how many threads to perform the conversion on</td>
    <td></td>
</tr>
</table>
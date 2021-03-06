# Zooniverse2

- [Zooniverse2](#zooniverse2)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Chunk extraction](#chunk-extraction)
    - [Chunk upload](#chunk-upload)

Split audios in chunks and uploads them to zooniverse.
Audio chunks and metadata are saved at a location specified by the user, allowing their later association with the results derived from Zooniverse.

Output metadata is stored as a dataframe, with the same format as [this example file](https://gist.github.com/lucasgautheron/4c7048ef11a05f2374ce2544b81c97d1).

## Installation

```bash
git clone https://github.com/LAAC-LSCP/Zooniverse2.git
cd Zooniverse2
pip install -r requirements.txt
```

## Usage

### Chunk extraction

```bash
python zooniverse.py extract-chunks [-h] --destination DESTINATION
                                    --sample-size SAMPLE_SIZE
                                    [--annotation-set ANNOTATION_SET]
                                    [--target-speaker-type {CHI,OCH,FEM,MAL}]
                                    [--batch-size BATCH_SIZE]
                                    [--threads THREADS]
                                    path
```

If it does not exist, DESTINATION is created.
Audio chunks are saved in wav and mp3 in `DESTINATION/chunks`.
Metadata is stored in a file named `DESTINATION/chunks.csv`.

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
    <td>sample-size</td>
    <td>how many vocalization events per recording</td>
    <td></td>
</tr>
<tr>
    <td>batch-size</td>
    <td>how many chunks per batch</td>
    <td>1000</td>
</tr>
<tr>
    <td>annotation-set</td>
    <td>which annotation set to use for sampling</td>
    <td>vtc</td>
</tr>
<tr>
    <td>target-speaker-type</td>
    <td>speaker type to get chunks from</td>
    <td>CHI</td>
</tr>
<tr>
    <td>threads</td>
    <td>how many threads to perform the conversion on, uses all CPUs if <= 0</td>
    <td>0</td>
</tr>
</table>

### Chunk upload


```bash
python zooniverse.py upload-chunks [-h] --destination DESTINATION
                                   --zooniverse-login ZOONIVERSE_LOGIN
                                   --zooniverse-pwd ZOONIVERSE_PWD
                                   --project-slug PROJECT_SLUG --subject-set
                                   SUBJECT_SET [--batches BATCHES]
```

Uploads as many batches of audio chunks as specified to Zooniverse, and updates `chunks.csv` accordingly.

<table>
<tr>
    <th>argument</th>
    <th>description</th>
    <th>default value</th>
</tr>
<tr>
    <td>destination</td>
    <td>where to find the output metadata and files.</td>
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
    <td>batches</td>
    <td>how many batches to upload. it is recommended to upload less than 10.000 chunks per day, so 10 batches of 1000 by default. upload all batches if set to 0</td>
    <td>0</td>
</tr>
</table>


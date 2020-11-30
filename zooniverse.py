#!/usr/bin/env python3
import argparse
import datetime
import itertools
import multiprocessing as mp
import os
import pandas as pd
from panoptes_client import Panoptes, Project, Subject, SubjectSet
import subprocess
import sys

from pydub import AudioSegment

from ChildProject.projects import ChildProject
from ChildProject.annotations import AnnotationManager

def check_dur(dur, target):
    if dur % 0.5 == 0:
        new_dur=dur
        remain=0
    else:
        closest_int=int(round(dur))
        if closest_int>=dur:
            new_dur = float(closest_int)
        else:
            new_dur = float(closest_int)+0.5
    remain = float(new_dur-dur)
    return new_dur,remain

class Chunk():
    def __init__(self, recording, onset, offset):
        self.recording = recording
        self.onset = onset
        self.offset = offset

    def getbasename(self, extension):
        return "{}_{}_{}.{}".format(
            os.path.splitext(self.recording.replace('/', '_'))[0],
            self.onset,
            self.offset,
            extension
        )

class ZooniversePipeline():
    def __init__(self, action, destination, path = "", project_slug = 'test', subject_set = 'test1', zooniverse_login = '', zooniverse_pwd = '', annotation_set = 'vtc',
            batch_size = 1000, target_speaker_type = 'CHI', sample_size = 500, chunk_length = 500, threads = 0, batches = 0, **kwargs):
        
        self.action = action
        self.project = ChildProject(path)

        self.batches = int(batches)
        self.project_slug = project_slug
        self.zooniverse_login = zooniverse_login
        self.zooniverse_pwd = zooniverse_pwd

        self.annotation_set = annotation_set
        self.destination = destination
        self.target_speaker_type = target_speaker_type
        self.sample_size = int(sample_size)
        self.batch_size = batch_size
        self.chunk_length = int(chunk_length)
        self.threads = int(threads)
        self.subject_set = subject_set
        
        assert 1000 % self.chunk_length == 0, 'chunk_length should divide 1000'

        self.chunks = []
                
    def split_recording(self, segments):
        segments = segments.sample(self.sample_size).to_dict(orient = 'records')

        source = os.path.join(self.project.path, 'recordings', segments[0]['recording_filename'])
        audio = AudioSegment.from_wav(source)

        for segment in segments:
            onset = int(segment['segment_onset']*1000)
            offset = int(segment['segment_offset']*1000)
            difference = offset-onset

            if difference < 1000:
                tgt = 1000-difference
                onset = float(onset)-tgt/2
                offset = float(offset) + tgt/2
            else:
                new_dur,remain = check_dur((offset-onset)/1000, self.chunk_length/1000)
                onset = float(onset)-remain*1000/2
                offset = float(offset) + remain*1000/2

            onset = int(onset)
            offset = int(offset)

            intervals = range(onset, offset, self.chunk_length) 
            chunks = []

            for interval in intervals:
                chunk = Chunk(segment['recording_filename'], interval, interval + self.chunk_length)
                chunk_audio = audio[chunk.onset:chunk.offset].fade_in(10).fade_out(10)

                wav = os.path.join(self.destination, 'chunks', chunk.getbasename('wav'))
                mp3 = os.path.join(self.destination, 'chunks', chunk.getbasename('mp3'))

                if not os.path.exists(wav):
                    chunk_audio.export(wav, format = 'wav')

                if not os.path.exists(mp3):
                    chunk_audio.export(mp3, format = 'mp3')

                chunks.append(chunk)

            return chunks

    def extract_chunks(self):
        am = AnnotationManager(self.project)
        self.annotations = am.annotations
        self.annotations = self.annotations[self.annotations['set'] == self.annotation_set]
        self.segments = am.get_segments(self.annotations)
        self.segments = self.segments[self.segments['speaker_type'] == self.target_speaker_type]
        self.segments['segment_onset'] = self.segments['segment_onset'] + self.segments['time_seek']
        self.segments['segment_offset'] = self.segments['segment_offset'] + self.segments['time_seek']

        destination_path = os.path.join(self.destination, 'chunks')
        os.makedirs(destination_path, exist_ok = True)
        if os.listdir(destination_path):
            raise ValueError("destination '{}' is not empty, please choose another destination.".format(destination_path))

        segments = []
        for _recording, _segments in self.segments.groupby('recording_filename'):
            segments.append(_segments.assign(recording_filename = _recording))
        
        pool = mp.Pool(self.threads if self.threads > 0 else mp.cpu_count())
        self.chunks = pool.map(self.split_recording, segments)
        self.chunks = itertools.chain.from_iterable(self.chunks)
        self.chunks = pd.DataFrame([{
            'recording': c.recording,
            'onset': c.onset,
            'offset': c.offset,
            'wav': c.getbasename('wav'),
            'mp3': c.getbasename('mp3'),
            'speaker_type': self.target_speaker_type,
            'date_extracted': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'uploaded': False,
            'zooniverse_id': 0
        } for c in self.chunks])

        # shuffle chunks so that they can't be joined back together
        # based on Zooniverse subject IDs
        self.chunks = self.chunks.sample(frac=1).reset_index(drop=True)
        self.chunks['batch'] = self.chunks.index.map(lambda x: int(x/self.batch_size))
        self.chunks.index.name = 'index'
        self.chunks.to_csv(os.path.join(self.destination, 'chunks.csv'))

    def upload_chunks(self):
        metadata_location = os.path.join(self.destination, 'chunks.csv')
        try:
            self.chunks = pd.read_csv(metadata_location, index_col = 'index')
        except:
            raise Exception("cannot read chunk metadata in {}. Check the --destination parameter, and make sure you have extracted chunks before.".format(metadata_location))

        Panoptes.connect(username = self.zooniverse_login, password = self.zooniverse_pwd)
        zooniverse_project = Project.find(slug = self.project_slug)

        subjects_metadata = []
        uploaded = 0
        for batch, chunks in self.chunks.groupby('batch'):
            if chunks['uploaded'].all():
                continue

            subject_set = SubjectSet()
            subject_set.links.project = zooniverse_project
            subject_set.display_name = "{}_batch_{}".format(self.subject_set, batch)
            subject_set.save()
            subjects = []

            _chunks = chunks.to_dict(orient = 'index')
            for chunk_index in _chunks:
                chunk = _chunks[chunk_index]

                print("uploading chunk {} ({},{}) in batch {}".format(chunk['recording'], chunk['onset'], chunk['offset'], batch))

                subject = Subject()
                subject.links.project = zooniverse_project
                subject.add_location(os.path.join(self.destination, 'chunks', chunk['mp3']))
                subject.metadata['date_extracted'] = chunk['date_extracted']
                subject.save()
                subjects.append(subject)

                chunk['index'] = chunk_index
                chunk['zooniverse_id'] = subject.id
                chunk['project_slug'] = self.project_slug
                chunk['subject_set'] = self.subject_set
                chunk['uploaded'] = True
                subjects_metadata.append(chunk)
            
            subject_set.add(subjects)

            self.chunks.update(
                pd.DataFrame(subjects_metadata).set_index('index')
            )

            self.chunks.to_csv(os.path.join(self.destination, 'chunks.csv'))
            uploaded += 1

            if self.batches > 0 and uploaded >= self.batches:
                return

    def run(self):
        if self.action == 'extract-chunks':
            self.extract_chunks()
        elif self.action == 'upload-chunks':
            self.upload_chunks()


parser = argparse.ArgumentParser(description = 'split audios un chunks and upload them to zooniverse')
subparsers = parser.add_subparsers(help = 'action', dest = 'action')

parser_extraction = subparsers.add_parser('extract-chunks', help = 'extract chunks')
parser_extraction.add_argument('path', help = 'path to the dataset')
parser_extraction.add_argument('--destination', help = 'destination', required = True)
parser_extraction.add_argument('--sample-size', help = 'how many samples per recording', required = True, type = int)
parser_extraction.add_argument('--annotation-set', help = 'annotation set', default = 'vtc')
parser_extraction.add_argument('--target-speaker-type', help = 'speaker type to get chunks from', default = 'CHI', choices=['CHI', 'OCH', 'FEM', 'MAL'])
parser_extraction.add_argument('--batch-size', help = 'batch size', default = 1000, type = int)
parser_extraction.add_argument('--threads', help = 'how many threads to run on', default = 0, type = int)

parser_upload = subparsers.add_parser('upload-chunks', help = 'upload chunks')
parser_upload.add_argument('--destination', help = 'destination', required = True)
parser_upload.add_argument('--zooniverse-login', help = 'zooniverse login', required = True)
parser_upload.add_argument('--zooniverse-pwd', help = 'zooniverse password', required = True)
parser_upload.add_argument('--project-slug', help = 'zooniverse project name', required = True)
parser_upload.add_argument('--subject-set', help = 'subject prefix', required = True)
parser_upload.add_argument('--batches', help = 'amount of batches to upload', required = False, type = int, default = 0)

args = parser.parse_args()

pipeline = ZooniversePipeline(**vars(args))
pipeline.run()
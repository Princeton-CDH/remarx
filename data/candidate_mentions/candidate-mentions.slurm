#!/bin/bash
#SBATCH --job-name=marx-title-candidates  # job short name 
#SBATCH --nodes=1                # node count
#SBATCH --ntasks=1               # total number of tasks across all nodes
#SBATCH --cpus-per-task=1       # cpu-cores per task 
#SBATCH --mem-per-cpu=2G        # memory per cpu-core
#SBATCH --gres=gpu:1
#SBATCH --time=00:55:00          # total run time limit (HH:MM:SS)
#SBATCH --mail-type=begin        # send email when job begins
#SBATCH --mail-type=end          # send email when job ends
#SBATCH --mail-type=fail         # send email if job fails
#SBATCH --mail-user=EMAIL@rinceton.edu

module purge
module load anaconda3/2024.6
conda activate marx
cd /scratch/gpfs/$USER/citing-marx
# configure stanza to reuse downloaded models from scratch folder
export STANZA_RESOURCES_DIR=/scratch/gpfs/$USER/.stanza_resources/
# title mentions run - completed in 30 minutes on 3 text files
#remarx-candidate-mentions candidate-texts/ title_mentions.csv --phrase "Das Manifest" "Manifesto" "Manifest" "Manifest der Kommunistischen Partei" "Kommunistische Manifest" "Das Kapital" "Kapital" "Erste Band das Kapital" "Erste Band" "Band"
# concept mentions - completed in 45 minutes on 26 text files
remarx-candidate-mentions candidate-texts/ concept_mentions.csv --phrase "industriellen Reservearmee" "Reservearmee" "Ursprünglichen Akkumulation" "Fetischcharakter der Ware"

